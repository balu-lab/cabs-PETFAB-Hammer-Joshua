import pyrealsense2 as rs
import numpy as np
import cv2
from ultralytics import YOLO

pipe = rs.pipeline()
cfg = rs.config()
cfg.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
cfg.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
profile = pipe.start(cfg)

depth_intrinsics = (
    profile.get_stream(rs.stream.depth)
    .as_video_stream_profile()
    .get_intrinsics()
)

align = rs.align(rs.stream.color)
model = YOLO("yolov8n.pt")

# Stores last known good 3D point per object label
last_known = {}  # { label: (dx, dy, dz) }

try:
    while True:
        frames = pipe.wait_for_frames()
        aligned_frames = align.process(frames)
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        width  = depth_frame.get_width()  // 2
        height = depth_frame.get_height() // 2
        distance_to_center = depth_frame.get_distance(width, height)
        print(f"Distance to frame center: {distance_to_center:.3f} m")

        results = model(color_image, conf=0.5, verbose=False, classes=[64])[0]

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf  = float(box.conf)
            label = model.names[int(box.cls)]

            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            z = depth_frame.get_distance(cx, cy)

            if z > 0:
                point = rs.rs2_deproject_pixel_to_point(
                    depth_intrinsics, [cx, cy], z
                )
                dx, dy, dz = point
                last_known[label] = (dx, dy, dz)  # update last known
                stale = False
            elif label in last_known:
                dx, dy, dz = last_known[label]    # fall back to last known
                stale = True
            else:
                dx = dy = dz = None               # never had a reading
                stale = False

            if dz is not None:
                tag = " (stale)" if stale else ""
                print(
                    f"{label:15s} | "
                    f"pixel=({cx:3d},{cy:3d}) | "
                    f"X={dx:+.3f} m  Y={dy:+.3f} m  Z={dz:+.3f} m"
                    f"{tag}"
                )
                caption = f"{label} {conf:.2f} | {dz:.2f}m{'*' if stale else ''}"
            else:
                print(f"{label:15s} | pixel=({cx:3d},{cy:3d}) | no depth reading")
                caption = f"{label} {conf:.2f} | --m"

            cv2.rectangle(color_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(color_image, caption, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        depth_cm = cv2.applyColorMap(
            cv2.convertScaleAbs(depth_image, alpha=0.03),
            cv2.COLORMAP_JET
        )
        cv2.imshow('rgb',   color_image)
        cv2.imshow('depth', depth_cm)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipe.stop()
    cv2.destroyAllWindows()
from detect_helper import *

img = "table.png"                  # an arm-camera photo, 640 x 480
W, H, HFOV = 640, 480, 60          # image size and horizontal field of view

dets = run_detector(img, conf=0.10)    # 1-2: photo and boxes, start low
dets = filter_by_score(dets, 0.50)     # 3: drop low scores
dets = nms(dets, 0.5)                  # 3: remove duplicate boxes
target = pick_target(dets, "cup")      # 4: the best cup, or None

if target is None:
    print("No cup found")
else:
    print("center:", box_center(target["box"]))
    dx, dy = pixel_offset(target["box"], W, H)
    print("offset:", dx, dy)
    # target on the right -> negative theta_B (it counts counter-clockwise)
    print("base turn (deg):", round(-turn_angle(dx, W, HFOV), 1))   # 5

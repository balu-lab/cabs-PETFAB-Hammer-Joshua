import math, numpy as np, cv2
from stereo_helper import *

cal = np.load("calibration.npz")
K1, d1, K2, d2 = cal["K1"], cal["d1"], cal["K2"], cal["d2"]
R, T = cal["R"], cal["T"]
size = tuple(int(v) for v in cal["size"])
CAM_POS = (100, 0, 150)       # where the camera sits in the base frame (mm)

left = cv2.imread("scene_left.png", cv2.IMREAD_GRAYSCALE)
right = cv2.imread("scene_right.png", cv2.IMREAD_GRAYSCALE)
left_r, right_r, f, cx, cy = rectify_pair(left, right, K1, d1, K2, d2,
                                          R, T, size)
B = baseline_mm(T)

disp = disparity_map(left_r, right_r, max_disp=160)
box = (500, 300, 700, 420)    # target box from the Lesson 9 detector,
                              # run on the rectified left image left_r
d = median_disparity(disp, box)
if d is None:
    print("No match inside the box")
else:
    Z = depth_from_disparity(d, f, B)
    u, v = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    p_base = camera_to_base(pixel_to_camera(u, v, Z, f, cx, cy), CAM_POS)
    dist = math.sqrt(sum(c * c for c in p_base))
    print(f"depth: {Z:.0f} mm")
    print("target in base frame (mm):", [round(c) for c in p_base])
    print(f"distance from base: {dist:.0f} mm ->",
          "reachable" if dist <= 500 else "too far")

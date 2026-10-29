import glob, numpy as np, cv2
from stereo_helper import *

PATTERN, SQUARE = (9, 6), 25.0         # inner corners, square size in mm
left_files = sorted(glob.glob("calib/left_*.png"))
right_files = sorted(glob.glob("calib/right_*.png"))

obj_pts, left_pts, right_pts = [], [], []
for lf, rf in zip(left_files, right_files):
    gl = cv2.imread(lf, cv2.IMREAD_GRAYSCALE)
    gr = cv2.imread(rf, cv2.IMREAD_GRAYSCALE)
    cl, cr = find_corners(gl, PATTERN), find_corners(gr, PATTERN)
    if cl is None or cr is None:
        print("skipped", lf)
        continue
    obj_pts.append(board_points(PATTERN, SQUARE))
    left_pts.append(cl)
    right_pts.append(cr)
size = (gl.shape[1], gl.shape[0])

rms1, K1, d1 = calibrate_camera(obj_pts, left_pts, size)
rms2, K2, d2 = calibrate_camera(obj_pts, right_pts, size)
rmsS, R, T = calibrate_stereo(obj_pts, left_pts, right_pts,
                              K1, d1, K2, d2, size)
print(f"pairs used: {len(obj_pts)}")
print(f"reprojection error (px): left {rms1:.2f}, right {rms2:.2f}, "
      f"stereo {rmsS:.2f}")
print(f"focal length (px): {K1[0, 0]:.1f}   "
      f"baseline (mm): {baseline_mm(T):.1f}")
np.savez("calibration.npz", K1=K1, d1=d1, K2=K2, d2=d2, R=R, T=T, size=size)

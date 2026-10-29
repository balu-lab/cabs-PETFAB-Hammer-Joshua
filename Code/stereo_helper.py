"""Helper functions for the Stereoscopic Camera lesson.
Pixel coordinates: (0, 0) is the TOP-LEFT of the image, x to the right, y down.
Lengths are in mm. Focal length f is measured in PIXELS.
Camera frame: x right, y down, z forward (out of the lens).
"""
import math
import numpy as np


# ---------- Day 1: disparity and depth ----------

def focal_px(image_width, hfov_deg):
    """Focal length in pixels from the image width and horizontal FOV."""
    return (image_width / 2) / math.tan(math.radians(hfov_deg) / 2)


def depth_from_disparity(d, f, baseline):
    """Z = f * B / d.  d and f in pixels, baseline and Z in mm."""
    return f * baseline / d


def disparity_from_depth(Z, f, baseline):
    """d = f * B / Z."""
    return f * baseline / Z


def pixel_to_camera(u, v, Z, f, cx, cy):
    """Pixel (u, v) at depth Z -> 3D point (X, Y, Z) in the camera frame."""
    return (u - cx) * Z / f, (v - cy) * Z / f, Z


def camera_to_base(p_cam, cam_pos):
    """Camera looks along the base +x axis, mounted at cam_pos = (x, y, z).
    Camera frame: X right, Y down, Z forward.
    Base frame: x forward, y left, z up."""
    X, Y, Z = p_cam
    return cam_pos[0] + Z, cam_pos[1] - X, cam_pos[2] - Y


# ---------- Day 2: calibration and disparity maps ----------

def board_points(pattern=(9, 6), square=25.0):
    """3D corner positions of a checkerboard lying flat (z = 0), in mm.
    pattern = number of INNER corners (columns, rows)."""
    pts = np.zeros((pattern[0] * pattern[1], 3), np.float32)
    pts[:, :2] = np.mgrid[0:pattern[0], 0:pattern[1]].T.reshape(-1, 2) * square
    return pts


def find_corners(gray, pattern=(9, 6)):
    """Find the checkerboard corners in a grayscale image (None if none)."""
    import cv2
    ok, corners = cv2.findChessboardCorners(gray, pattern)
    if not ok:
        return None
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    return cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), crit)


def calibrate_camera(obj_points, img_points, image_size):
    """One camera. Returns (rms_error_px, K, dist).
    K = [[fx, 0, cx], [0, fy, cy], [0, 0, 1]] is the intrinsic matrix."""
    import cv2
    rms, K, dist, _, _ = cv2.calibrateCamera(obj_points, img_points,
                                             image_size, None, None)
    return rms, K, dist


def calibrate_stereo(obj_points, left_pts, right_pts, K1, d1, K2, d2,
                     image_size):
    """Two cameras. Returns (rms_error_px, R, T): the rotation and translation
    from the left camera to the right camera. |T| is the baseline."""
    import cv2
    flags = cv2.CALIB_FIX_INTRINSIC
    rms, _, _, _, _, R, T, _, _ = cv2.stereoCalibrate(
        obj_points, left_pts, right_pts, K1, d1, K2, d2, image_size,
        flags=flags)
    return rms, R, T


def baseline_mm(T):
    return float(np.linalg.norm(T))


def disparity_map(left_gray, right_gray, max_disp=160, block=5):
    """Disparity in pixels for every pixel (images must be rectified).
    max_disp must be a multiple of 16. Nothing closer than f * B / max_disp
    is seen. With f = 700 px and B = 60 mm, 160 reaches down to 263 mm."""
    import cv2
    sgbm = cv2.StereoSGBM_create(minDisparity=0, numDisparities=max_disp,
                                 blockSize=block,
                                 P1=8 * block * block, P2=32 * block * block,
                                 uniquenessRatio=10)
    return sgbm.compute(left_gray, right_gray).astype(np.float32) / 16.0


def rectify_pair(left, right, K1, d1, K2, d2, R, T, image_size):
    """Warp both images so matching points lie on the same row.
    Returns (left_rect, right_rect, f, cx, cy): the focal length and principal
    point (px) of the rectified cameras. Use THESE in Z = f * B / d, not the
    old values."""
    import cv2
    R1, R2, P1, P2, Q, _, _ = cv2.stereoRectify(K1, d1, K2, d2, image_size,
                                                R, T, alpha=0)
    m1 = cv2.initUndistortRectifyMap(K1, d1, R1, P1, image_size, cv2.CV_32FC1)
    m2 = cv2.initUndistortRectifyMap(K2, d2, R2, P2, image_size, cv2.CV_32FC1)
    left_rect = cv2.remap(left, m1[0], m1[1], cv2.INTER_LINEAR)
    right_rect = cv2.remap(right, m2[0], m2[1], cv2.INTER_LINEAR)
    f, cx, cy = float(P1[0, 0]), float(P1[0, 2]), float(P1[1, 2])
    return left_rect, right_rect, f, cx, cy


def median_disparity(disp, box):
    """Median disparity inside a box (x_min, y_min, x_max, y_max), ignoring
    pixels where no match was found. Returns None if nothing matched."""
    x1, y1, x2, y2 = [int(v) for v in box]
    patch = disp[y1:y2, x1:x2]
    good = patch[patch > 0]
    return float(np.median(good)) if good.size else None


if __name__ == "__main__":
    f = 700
    print(round(depth_from_disparity(14, f, 60)))  # expected: 3000

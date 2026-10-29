# Lesson 10: Stereoscopic Camera

Students give the arm a sense of distance. In Lesson 9, a bounding box told the arm which way to turn, but not how far to reach. Two cameras a fixed distance apart see the same object in slightly different places, and that shift tells us how far away the object is. On Day 1 students define disparity, use Z = f · B ÷ d to turn it into depth, and find out why depth gets less accurate as objects get farther away. On Day 2 they calibrate a stereo camera with a checkerboard, learn what rectification and a disparity map are, and turn a pixel and its depth into an (x, y, z) point in the arm's base frame. That point is the target that inverse kinematics from Lessons 6 to 8 turns into joint angles.

**Time:** two class periods (about 60 minutes each)

## Objectives

By the end of this lesson, students will be able to:

- Explain why one camera cannot measure distance, and why two views of the same scene can
- Measure the disparity of a point from its pixel columns in the left and right images
- Use Z = f · B ÷ d to find depth, and rearrange it to find the disparity expected at a given depth
- Explain how the baseline and the distance to the object change the accuracy of the depth
- Describe what calibration finds (intrinsics, distortion, and the rotation and translation between the two cameras) and capture a checkerboard set to find it
- Judge a calibration from its reprojection error and its measured baseline
- Explain what rectification does, read a disparity map and find the closest depth it can measure
- Turn a pixel and its depth into a 3D point in the camera frame, and then into the arm's base frame

## Files

| File | What it is |
|------|------------|
| [Lesson Plan 10 - Stereoscopic Camera.pdf](Lesson%20Plan%2010%20-%20Stereoscopic%20Camera.pdf) | Lesson plan with timed procedures, worked answers and assessment |
| [Lesson Plan 10 - Stereoscopic Camera.docx](Lesson%20Plan%2010%20-%20Stereoscopic%20Camera.docx) | Lesson plan (Word, editable) |
| [Lesson_10_Stereoscopic_Camera.pdf](Lesson_10_Stereoscopic_Camera.pdf) | Slides (PDF) |
| [Lesson_10_Stereoscopic_Camera.pptx](Lesson_10_Stereoscopic_Camera.pptx) | Slides (PowerPoint, editable) |

## The formulas

1. Disparity: d = x_L − x_R, in pixels
2. Depth: Z = f · B ÷ d, with f in pixels and B and Z in mm
3. Closest depth the matcher can see: Z_min = f · B ÷ max_disp
4. Pixel to camera frame: X = (u − cx) · Z ÷ f and Y = (v − cy) · Z ÷ f
5. Camera frame to base frame (camera looking along the arm's +x): x_b = cam_x + Z, y_b = cam_y − X and z_b = cam_z − Y

The worked example puts the camera at (100, 0, 150) mm and turns the camera-frame point (34.3, 25.7, 300) into the base-frame target (400, −34.3, 124.3), 420.3 mm from the base and inside the arm's 500 mm reach, with θB = atan2(−34.3, 400) = −4.9°. The slides use B = 60 mm. The arm's RealSense D435i has B = 50 mm.

## Code

The code for this lesson is in the [Code folder](../../Code/). Install the packages with `pip install numpy opencv-python`. Keep the files in one folder, because the scripts import `stereo_helper.py`. The Day 2 target script also uses the box from the Lesson 9 detector ([`detect_helper.py`](../../Code/detect_helper.py)).

| Day | File | What it does |
|-----|------|--------------|
| 1–2 | [`stereo_helper.py`](../../Code/stereo_helper.py) | `focal_px`, `depth_from_disparity`, `disparity_from_depth`, `pixel_to_camera`, `camera_to_base`, and the calibration, rectification and disparity map functions |
| 1 | [`stereo_depth_check.py`](../../Code/stereo_depth_check.py) | Turns the columns read from the left and right images into a depth. Prints 292 mm for the slide's numbers |
| 2 | [`stereo_calibrate.py`](../../Code/stereo_calibrate.py) | Finds the checkerboard corners in the pairs in a `calib` folder (`left_00.png`, `right_00.png` and so on), calibrates both cameras and saves `calibration.npz` |
| 2 | [`stereo_target.py`](../../Code/stereo_target.py) | Rectifies a stereo pair (`scene_left.png`, `scene_right.png`), makes a disparity map, reads the depth inside the target box and prints the target in the base frame and whether it is in reach |

`disparity_map` searches up to 160 px of disparity by default. With f = 700 px and B = 60 mm, that reaches down to about 263 mm, which covers the arm's 300 to 500 mm working range. The scripts were tested on rendered images: calibration found f = 700.9 px and B = 59.8 mm (true values 700 and 60), and a target 300 mm away was measured at 301 mm. Do one full calibration with the real camera before class.

**Previous:** [Lesson 9: AI Object Detection](../Lesson%209/)

# PETFAB Armadillo – 4-DOF Educational Robotic Arm

This repository contains the assembly instructions, curriculum, and control software to build and run the PETFAB Armadillo, a 4-DOF robotic arm designed for high school robotics, kinematics, and computer vision courses.

## Contents

- **Assembly Instructions** – step-by-step build guide for the base, shoulder, elbow, gripper, and full arm (PowerPoint + PDF)
- **Curriculum** – a 12-lesson course outline plus lesson plans and slides for Lessons 1–3
- **Code** – waypoint teach/replay GUI and a vision/object-detection test program
- **3D Printing Files** – printable links, plates, and gripper parts *(coming soon)*
- **CAD** – design source files *(coming soon)*
- **User Manuals** – actuator and camera datasheets *(coming soon)*

## Specs

- 4 degrees of freedom: base, shoulder, elbow, wrist
- Underactuated two-finger, spring-loaded gripper driven by a cable coiler
- Robotis Dynamixel XM540-W270-T actuators (with motor, gearbox, and encoder) at every joint and the gripper
- Base driven through a 12T to 36T gear (3:1 reduction) on a bearing-supported turntable
- 3D-printed rigid links with M2.5 / M3 / M5 hardware
- Intel RealSense D435i depth camera mounted on the arm for object detection
- Controlled from a PC over Dynamixel Protocol 2.0 at 1 Mbps

## Getting Started

1. Purchase the parts listed in the Bill of Materials *(coming soon)*.
2. Print the 3D-printed parts.
3. Build the arm following `Assembly Instructions/All Assembly Instructions.pdf`.
4. Install Python 3 and the requirements:
   ```
   pip install -r Code/requirements.txt
   ```
5. In `Code/waypoint.py`, set `DEVICENAME` to your serial port (for example `COM5` on Windows).
6. Run the waypoint GUI:
   ```
   python Code/waypoint.py
   ```
   To load and replay a saved sequence automatically: `python Code/waypoint.py sequence.json`
7. To test the camera and object detection: `python Code/vision_object_detection_test.py`. Press `q` to quit.

## Code

| File | What it does |
|------|--------------|
| `waypoint.py` | Tkinter GUI for jogging the arm with inverse kinematics, teaching waypoints by hand (torque off), opening and closing the gripper, and saving and replaying waypoint sequences as JSON. Runs without hardware for previewing. |
| `vision_object_detection_test.py` | Streams color and depth from the RealSense D435i, runs YOLOv8n object detection, and prints each detected object's 3D position in meters. |

## Educational Use

The curriculum takes students from building the arm through forward kinematics, inverse kinematics, and stereo vision with AI object detection. It ends in a capstone challenge where the arm finds and moves to an object on its own. It is aligned with NGSS engineering design standards (HS-ETS1-1 to HS-ETS1-4).

| # | Lesson | Status |
|---|--------|--------|
| 1 | Introduction to the Robotic Arm | Included |
| 2 | Building the Robotic Arm | Included |
| 3 | Trigonometric Approach to FK | Included |
| 4 | Denavit-Hartenberg Approach to FK | Planned |
| 5 | Code Implementation of FK | Planned |
| 6 | Trigonometric Approach to IK | Planned |
| 7 | Gradient Descent Approach to IK | Planned |
| 8 | Code Implementation of IK | Planned |
| 9 | Stereoscopic Camera | Planned |
| 10 | AI Object Detection | Planned |
| 11 | Stereoscopic Vision & AI Object Detection | Planned |
| 12 | Challenge: Move Object | Planned |

Prerequisites: high school Math 3 / Geometry and intermediate Python.

## Safety

- Keep fingers out of the gap between the upper and lower arm segments (pinch point).
- Stay clear of the arm while it is powered.
- If the arm moves unexpectedly, cut power immediately.

## Credits

- Original design, assembly instructions, curriculum, and software by Joseph Ruhan
- CABS Lab, NC A&T State University

## Third-Party Software

- Dynamixel SDK (Apache-2.0) – https://github.com/ROBOTIS-GIT/DynamixelSDK
- Intel RealSense SDK / pyrealsense2 (Apache-2.0) – https://github.com/IntelRealSense/librealsense
- Ultralytics YOLOv8 (AGPL-3.0) – https://github.com/ultralytics/ultralytics

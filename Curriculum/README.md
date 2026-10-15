# Curriculum

A 12-lesson course that takes high school students from building the PETFAB Armadillo to making it find and move an object on its own. Lessons 1–5 are ready to teach. Lessons 6–12 are planned.

The course is built around three questions, introduced in Lesson 1 and revisited throughout:

1. **How does the arm know where it is?** Forward kinematics (Lessons 3–5)
2. **How does the arm know where to go?** Inverse kinematics (Lessons 6–8)
3. **How can the arm interact with the world?** Computer vision and AI object detection (Lessons 9–11)

The full course description, learning goals, standards alignment and materials list are in [Robotic Arm Lessons Overview.docx](Robotic%20Arm%20Lessons%20Overview.docx).

## Lessons

| # | Lesson | What students do | Status |
|---|--------|------------------|--------|
| 1 | [Introduction to the Robotic Arm](Lesson%201/) | Vocabulary, parts, safety, industry context | Included |
| 2 | [Building the Robotic Arm](Lesson%202/) | Physical assembly, wiring, functional testing | Included |
| 3 | [Trigonometric Approach to FK](Lesson%203/) | Derive forward kinematics with trigonometry in 2D and 3D | Included |
| 4 | [Denavit-Hartenberg Approach to FK](Lesson%204/) | Forward kinematics with DH parameters and matrices | Included |
| 5 | [Code Implementation of FK](Lesson%205/) | Code forward kinematics, preview screw theory, map the arm's reach | Included |
| 6 | Trigonometric Approach to IK | Derive inverse kinematics with the law of cosines and trigonometry | Planned |
| 7 | Gradient Descent Approach to IK | Iterative, numerical inverse kinematics | Planned |
| 8 | Code Implementation of IK | Code inverse kinematics, preview Jacobians | Planned |
| 9 | Stereoscopic Camera | Depth perception through disparity, camera calibration | Planned |
| 10 | AI Object Detection | Pretrained object detection models, bounding boxes | Planned |
| 11 | Stereoscopic Vision & AI Object Detection | Combine detection and depth to locate objects in 3D | Planned |
| 12 | Challenge: Move Object | Full pipeline; autonomous pick-and-place demo | Planned |

Each lesson folder has a lesson plan (objectives, timed procedures and an assessment) and the slides it refers to.

## Prerequisites

High school Math 3 / Geometry and intermediate Python.

## Assessment

Every lesson ends with a short formative assessment tied to its objectives. The coding lessons (5, 8 and 11) are assessed mainly through working code checked against known test cases. The course ends with Lesson 12's live challenge, where teams show their arm detecting and moving to a target object on its own.

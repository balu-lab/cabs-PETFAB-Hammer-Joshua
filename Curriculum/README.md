# Curriculum

A 10-lesson course that takes high school students from building the PETFAB Armadillo to programming how it moves and how it sees. Lessons 1–7, 9 and 10 are ready to teach. Lesson 8 is planned.

The course is built around three questions, introduced in Lesson 1 and revisited throughout:

1. **How does the arm know where it is?** Forward kinematics (Lessons 3–5)
2. **How does the arm know where to go?** Inverse kinematics (Lessons 6–8)
3. **How can the arm interact with the world?** AI object detection and stereo vision (Lessons 9–10)

The full course description, learning goals, standards alignment and materials list are in [Robotic Arm Lessons Overview.docx](Robotic%20Arm%20Lessons%20Overview.docx).

## Lessons

| # | Lesson | What students do | Status |
|---|--------|------------------|--------|
| 1 | [Introduction to the Robotic Arm](Lesson%201/) | Vocabulary, parts, safety, industry context | Included |
| 2 | [Building the Robotic Arm](Lesson%202/) | Physical assembly, wiring, functional testing | Included |
| 3 | [Trigonometric Approach to FK](Lesson%203/) | Derive forward kinematics with trigonometry in 2D and 3D | Included |
| 4 | [Denavit-Hartenberg Approach to FK](Lesson%204/) | Forward kinematics with vectors and the DH angle convention, in 2D and 3D, checked in Desmos | Included |
| 5 | [Code Implementation of FK](Lesson%205/) | Code forward kinematics one function at a time, compare it with Lesson 3's method, map the arm's reach | Included |
| 6 | [Trigonometric Approach to IK](Lesson%206/) | Derive inverse kinematics with the law of cosines and trigonometry | Included |
| 7 | [Gradient Descent Approach to IK](Lesson%207/) | Iterative, numerical inverse kinematics | Included |
| 8 | Code Implementation of IK | Code inverse kinematics, preview Jacobians | Planned |
| 9 | [AI Object Detection](Lesson%209/) | Find objects with a pretrained detector, clean up the boxes and turn the base toward a target | Included |
| 10 | [Stereoscopic Camera](Lesson%2010/) | Depth from disparity, camera calibration and 3D target points for the arm | Included |

Each lesson folder has a lesson plan (objectives, timed procedures and an assessment) and the slides it refers to.

## Prerequisites

High school Math 3 / Geometry and intermediate Python.

## Assessment

Every lesson ends with a short formative assessment tied to its objectives. The coding lessons (5 and 8) are assessed mainly through working code checked against known test cases.

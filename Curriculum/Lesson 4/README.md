# Lesson 4: Denavit-Hartenberg Approach to Forward Kinematics

Students learn the Denavit-Hartenberg (DH) method, a repeatable recipe for forward kinematics in which every joint becomes one matrix. On Day 1 they write rotations and moves as matrices and chain them to solve the 2-link arm from Lesson 3. On Day 2 they place a coordinate frame on each joint, fill in a DH table for the 3D arm, build one matrix per joint and multiply them.

**Time:** two class periods (about 60 minutes each)

## Objectives

By the end of this lesson, students will be able to:

- Write a rotation and a move as matrices and chain them to find the end-effector position of the 2-link arm
- Explain why the order of matrix multiplication matters
- Place a coordinate frame on each joint and fill in the DH table (θ, d, a, α) for the base, shoulder and elbow
- Build one DH matrix per joint and multiply them to calculate the 3D end-effector position
- Check the DH result against the Lesson 3 trigonometric result and compare the two methods

## Files

| File | What it is |
|------|------------|
| [Lesson Plan 4 - Denavit-Hartenberg Approach to FK.pdf](Lesson%20Plan%204%20-%20Denavit-Hartenberg%20Approach%20to%20FK.pdf) | Lesson plan with timed procedures, worked answers and assessment |
| [Lesson Plan 4 - Denavit-Hartenberg Approach to FK.docx](Lesson%20Plan%204%20-%20Denavit-Hartenberg%20Approach%20to%20FK.docx) | Lesson plan (Word, editable) |
| [Lesson_4_DH_Approach_to_FK_plain_colours.pdf](Lesson_4_DH_Approach_to_FK_plain_colours.pdf) | Slides (PDF) |
| [Lesson_4_DH_Approach_to_FK_plain_colours.pptx](Lesson_4_DH_Approach_to_FK_plain_colours.pptx) | Slides (PowerPoint, editable) |

The `dh_helper.py` code used on the "Check It with Code" slide is in the lesson plan's appendix.

## Check your DH result

Done correctly, the DH method gives the same end-effector position as the trigonometric method from Lesson 3. Use the Lesson 3 Desmos model to check your answers:
[Open the Desmos graph](https://www.desmos.com/3d/9bnvqc263x)

**Previous:** [Lesson 3](../Lesson%203/) · **Next:** [Lesson 5: Code Implementation of FK](../Lesson%205/)

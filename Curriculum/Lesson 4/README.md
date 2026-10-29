# Lesson 4: The DH Approach to Forward Kinematics

Students find where the tip of the arm is with vectors, using the DH (Denavit-Hartenberg) convention that engineers use for robot arms: each joint angle is measured from the link before it, and up (counterclockwise) is positive. On Day 1 they use the flat arm from Lesson 3. They write the upper arm as an arrow (cos θS, sin θS), turn that arrow 90° to get a second arrow at a right angle, and use the two arrows to find the direction of the forearm from the elbow angle. Adding the link vectors gives the tip. On Day 2 the base turn gives each arrow a third number, and students check their answers in the Desmos graph. No matrices are used.

**Time:** two class periods (about 60 minutes each)

## Objectives

By the end of this lesson, students will be able to:

- Measure joint angles with the DH convention, and change Lesson 3 angles into DH angles
- Write a link as a unit vector (cos θ, sin θ) times the link's length
- Turn a vector 90° with (x, y) → (−y, x)
- Find the forearm's direction with f = cos θE · e + sin θE · n
- Add the link vectors in a link table to find the tip of the arm, in 2D and in 3D
- Check answers with the Desmos DH graph and explain what each part of the graph does

## Files

| File | What it is |
|------|------------|
| [Updated_Lesson Plan 4_ Vector Approach to FK.pdf](Updated_Lesson%20Plan%204_%20Vector%20Approach%20to%20FK.pdf) | Lesson plan with timed procedures, worked answers and assessment |
| [Updated_Lesson Plan 4_ Vector Approach to FK.docx](Updated_Lesson%20Plan%204_%20Vector%20Approach%20to%20FK.docx) | Lesson plan (Word, editable) |
| [Updated_Lesson_4_Vector_Approach_to_FK.pdf](Updated_Lesson_4_Vector_Approach_to_FK.pdf) | Slides (PDF) |
| [Updated_Lesson_4_Vector_Approach_to_FK.pptx](Updated_Lesson_4_Vector_Approach_to_FK.pptx) | Slides (PowerPoint, editable) |

## Angles

| Angle | What it measures | From Lesson 3 |
|-------|------------------|---------------|
| θB (base) | How far the base has turned from the x-axis, looking down from above | θB = θ3 |
| θS (shoulder) | The upper arm, measured up from the floor | θS = 90° − θ1 |
| θE (elbow) | The forearm, measured from the line of the upper arm (negative when the elbow bends down) | θE = −θ2 |

The worked example uses L1 = L2 = 250 mm and θB = 45°, θS = 45°, θE = −45°. The flat arm's tip is (426.78, 176.78), and with the base turn the tip is (301.78, 301.78, 176.78), the same answers as Lesson 3.

## Check your answers in Desmos

The Lesson 4 Desmos graph uses the DH convention:
[Open the Desmos graph](https://www.desmos.com/3d/qq1w1zrs78)

Set u = θB, v = θS and w = θE, then read d. The graph measures in hundreds of mm, so multiply d by 100: the worked example gives d = (3.0178, 3.0178, 1.7678), which is (301.78, 301.78, 176.78) mm. In the Vectors folder, click the gray circles to show the hidden arrows (the frames).

**Previous:** [Lesson 3](../Lesson%203/) · **Next:** [Lesson 5: Code Implementation of FK](../Lesson%205/)

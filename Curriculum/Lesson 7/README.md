# Lesson 7: Gradient Descent Approach to Inverse Kinematics

Students meet iterative (numerical) inverse kinematics. Instead of solving for the angles with triangles as in Lesson 6, the robot improves a guess: it uses forward kinematics to find where the tip lands, measures the error, and nudges every joint a little "downhill" so the error gets smaller. On Day 1 students do this by hand for one number, for one joint and for the flat arm. On Day 2 they extend the same loop to the 3D arm and study the results of a computer run: they choose a learning rate and see what happens with different start poses, targets that are out of reach and targets near full reach.

**Time:** two class periods (about 60 minutes each)

## Objectives

By the end of this lesson, students will be able to:

- Describe iterative IK as guess, measure the error, improve, and explain why it only needs forward kinematics
- Write the cost as the squared error in link lengths, and estimate a slope by nudging a joint
- Apply the step rule θ_new = θ − η × slope by hand to one number, one joint and the flat arm
- Extend gradient descent IK to the 3D arm and choose a sensible learning rate, tolerance and step limit
- Explain what happens when the target is out of reach, near full reach or approached from a different start pose, and always check the final error
- Compare gradient descent with the trigonometric method of Lesson 6

## Files

| File | What it is |
|------|------------|
| [Lesson Plan 7 - Gradient Descent Approach to IK.pdf](Lesson%20Plan%207%20-%20Gradient%20Descent%20Approach%20to%20IK.pdf) | Lesson plan with timed procedures, worked answers and assessment |
| [Lesson Plan 7 - Gradient Descent Approach to IK.docx](Lesson%20Plan%207%20-%20Gradient%20Descent%20Approach%20to%20IK.docx) | Lesson plan (Word, editable) |
| [Lesson_7_Gradient_Descent_Approach_to_IK.pdf](Lesson_7_Gradient_Descent_Approach_to_IK.pdf) | Slides (PDF) |
| [Lesson_7_Gradient_Descent_Approach_to_IK.pptx](Lesson_7_Gradient_Descent_Approach_to_IK.pptx) | Slides (PowerPoint, editable) |

## The method

1. Cost: C = (error ÷ 250)², the squared error measured in link lengths
2. Slope: nudge a joint a tiny amount h and see how the cost changes, (C(θ + h) − C(θ)) ÷ h
3. Step: θ_new = θ − η × slope, for every joint at once (in radians)
4. Repeat until the error is under the tolerance (0.5 mm) or the step limit (1000 steps) is reached, then check the final error

All angles use the DH convention from Lessons 4–6, with L1 = L2 = 250 mm. There is no code in this lesson: the Day 2 slides show the results of a computer run (start (0°, 45°, −45°), η = 0.1). Students write the IK code themselves in [Lesson 8](../Lesson%208/).

**Previous:** [Lesson 6](../Lesson%206/) · **Next:** [Lesson 8: Code Implementation of IK](../Lesson%208/)

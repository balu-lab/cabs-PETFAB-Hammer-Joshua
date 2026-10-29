# Lesson 5: Code Implementation of Forward Kinematics and Other Methods

Students turn the DH steps from Lesson 4 into Python code, one small function at a time. On Day 1 they write `arrow`, `scale`, `add_vectors`, `turn_90`, `turn` and `flat_tip` for the flat arm, check each one against the answers from Lesson 4, and hunt for three common bugs. On Day 2 they write `arrow_3d` and `turned_3d` for the base turn, reuse the same steps in `tip_3d` to find the 3D position, check it in the Lesson 4 Desmos graph, and compare it with Lesson 3's method written as code. Then they use loops to try many poses and see where the tip can reach. Every student finishes with a short Python program that finds the end effector position from the joint angles. Students need intermediate Python: variables, functions, lists, for loops and import.

**Time:** two class periods (about 60 minutes each)

## Objectives

By the end of this lesson, students will be able to:

- Use `math.radians` with `math.sin` and `math.cos` to work with angles in degrees
- Write a function that returns a link's arrow (cos θ, sin θ) from its angle
- Write functions that multiply a vector by a number and add two vectors with a for loop
- Turn an arrow 90° and by any angle in code, with the rules from Lesson 4
- Build `flat_tip` and `tip_3d` from these small functions, and check them against the answers from Lesson 4
- Find a bug by checking code against an answer they already know
- Compare two methods in code (Lesson 3's trigonometry and Lesson 4's DH steps) and change Lesson 3 angles into DH angles
- Use loops to try many poses and describe the region the tip can reach

## Files

| File | What it is |
|------|------------|
| [Lesson Plan 5 - Code Implementation of Forward Kinematics and Other Methods.pdf](Lesson%20Plan%205%20-%20Code%20Implementation%20of%20Forward%20Kinematics%20and%20Other%20Methods.pdf) | Lesson plan with timed procedures and assessment |
| [Lesson Plan 5 - Code Implementation of Forward Kinematics and Other Methods.docx](Lesson%20Plan%205%20-%20Code%20Implementation%20of%20Forward%20Kinematics%20and%20Other%20Methods.docx) | Lesson plan (Word, editable) |
| [Lesson_5_Code_Implementation_of_FK.pdf](Lesson_5_Code_Implementation_of_FK.pdf) | Slides (PDF) |
| [Lesson_5_Code_Implementation_of_FK.pptx](Lesson_5_Code_Implementation_of_FK.pptx) | Slides (PowerPoint, editable) |

## Code

The code for this lesson is in the [Code folder](../../Code/). It needs only Python 3 (matplotlib is used just for the optional plot). Keep the files in one folder, because `reach_sweep.py` and `reach_plot.py` import `arm.py`.

| Day | File | Who it's for | What to do with it |
|-----|------|--------------|--------------------|
| 1 | [`arm_starter.py`](../../Code/arm_starter.py) | Students | Save a copy as `arm.py` and add the functions one step at a time |
| 1–2 | [`arm.py`](../../Code/arm.py) | Teacher | Solution: `arrow`, `scale`, `add_vectors`, `turn_90`, `turn`, `flat_tip`, `arrow_3d`, `turned_3d`, `tip_3d` and Lesson 3's `trig_tip`. Hold it back until students have tried the steps themselves |
| 2 | [`reach_sweep.py`](../../Code/reach_sweep.py) | Students | Tries 100 poses and prints the farthest (500.0 mm) and nearest (353.55 mm) tip |
| 2 | [`reach_plot.py`](../../Code/reach_plot.py) | Students (optional) | Draws the same poses as a picture of the reachable region |

Check your code with the worked example: `show(flat_tip(45, -45))` prints `[426.78, 176.78]` and `show(tip_3d(45, 45, -45))` prints `[301.78, 301.78, 176.78]`.

The code uses link lengths of L1 = L2 = 250 mm, as in Lessons 3 and 4, and the DH angles from Lesson 4: θB is the base turn, θS is measured from the floor, θE is measured from the line of the upper arm, and up is +. If your arm measures differently, change the two constants at the top of `arm.py`. The answers on the slides will change too.

**Previous:** [Lesson 4](../Lesson%204/)

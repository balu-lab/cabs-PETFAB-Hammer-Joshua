# Lesson 5: Code Implementation of Forward Kinematics and Other Methods

Students turn the forward kinematics from Lessons 3 and 4 into working Python code. On Day 1 they write `dh_matrix` and `forward_kinematics` and check them with a pass/fail test. On Day 2 they compare the code with Lesson 3's trigonometry, try a second method (screw theory), and sweep through many poses to map where the arm's tip can reach. Every student finishes with a tested `forward_kinematics` function that the inverse kinematics lessons build on.

**Time:** two class periods (about 60 minutes each)

## Objectives

By the end of this lesson, students will be able to:

- Translate the arm's DH table into Python, with one `dh_matrix` call per table row
- Write a `forward_kinematics` function that multiplies the joint matrices with NumPy and returns the tip position (x, y, z)
- Test the function against hand-calculated answers and name the two most common bugs (degrees vs. radians, and the order of multiplication)
- Describe screw theory as a second method for forward kinematics, run it, and confirm it agrees with the DH result
- Sweep through many joint angles and describe the region the arm's tip can reach

## Files

| File | What it is |
|------|------------|
| [Lesson Plan 5_ Code Implementation of Forward Kinematics and Other Methods (1).pdf](Lesson%20Plan%205_%20Code%20Implementation%20of%20Forward%20Kinematics%20and%20Other%20Methods%20%281%29.pdf) | Lesson plan with timed procedures and assessment |
| [Lesson Plan 5_ Code Implementation of Forward Kinematics and Other Methods (1).docx](Lesson%20Plan%205_%20Code%20Implementation%20of%20Forward%20Kinematics%20and%20Other%20Methods%20%281%29.docx) | Lesson plan (Word, editable) |
| [Lesson_5_Code_Implementation_of_FK (1).pdf](Lesson_5_Code_Implementation_of_FK%20%281%29.pdf) | Slides (PDF) |
| [Lesson_5_Code_Implementation_of_FK (2).pptx](Lesson_5_Code_Implementation_of_FK%20%282%29.pptx) | Slides (PowerPoint, editable) |

## Code

The code for this lesson is in the [Code folder](../../Code/). It needs Python 3 and NumPy, plus matplotlib for the reach plot. Keep the files in one folder, since several of them import `fk.py` or `screw_helper.py`.

| Day | File | Who it's for | What to do with it |
|-----|------|--------------|--------------------|
| 1 | [`fk_starter.py`](../../Code/fk_starter.py) | Students | Save a copy as `fk.py` and fill in the two functions |
| 1 | [`check_fk.py`](../../Code/check_fk.py) | Students | Run next to `fk.py` to get PASS/FAIL against known answers |
| 1 | [`fk.py`](../../Code/fk.py) | Teacher | Solution for Day 1 |
| 2 | [`compare_methods.py`](../../Code/compare_methods.py) | Teacher | Checks the DH code against Lesson 3's trigonometry |
| 2 | [`screw_helper.py`](../../Code/screw_helper.py) | Students | Helper functions for screw theory |
| 2 | [`fk_screw_starter.py`](../../Code/fk_screw_starter.py) | Students | Save a copy as `fk_screw.py` and fill in one line |
| 2 | [`fk_screw.py`](../../Code/fk_screw.py) | Teacher | Solution for the screw theory exercise |
| 2 | [`workspace_sweep.py`](../../Code/workspace_sweep.py) | Students | Plots where the arm's tip can reach |

The code uses link lengths of L1 = L2 = 250 mm, as in Lessons 3 and 4. If your arm measures differently, change the two constants at the top of `fk.py` and the expected answers in `check_fk.py`.

**Previous:** [Lesson 4](../Lesson%204/)

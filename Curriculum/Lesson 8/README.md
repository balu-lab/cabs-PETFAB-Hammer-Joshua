# Lesson 8: Code Implementation of Inverse Kinematics and Other Methods

Students write the two inverse kinematics (IK) methods from Lessons 6 and 7 as Python code, one small function at a time, and check every answer with the forward kinematics (FK) code from Lesson 5. On Day 1 they turn Lesson 6's triangles into `law_of_cosines`, `elbow`, `shoulder`, `ik_flat` and `ik_3d`, and handle targets that are out of reach with `raise` and `try`/`except`. On Day 2 they turn Lesson 7's gradient descent into `error`, `cost`, `slopes` and the `ik_gd` loop, test learning rates and run both methods on the same targets. Then they meet the Jacobian, a table that says how each joint moves the tip, and see that a Jacobian method needs far fewer steps. They also find Lesson 6's steps inside the arm's own control program, `waypoint.py`.

**Time:** two class periods (about 60 minutes each)

## Objectives

By the end of this lesson, students will be able to:

- Use `math.acos`, `math.atan2` and `math.degrees` to turn a number back into an angle in degrees
- Write Lesson 6's recipe as small functions (`law_of_cosines`, `elbow`, `shoulder`, `ik_flat` and `ik_3d`) and check each one against the answers from Lesson 6
- Check every IK answer with FK from Lesson 5
- Use `raise` and `try`/`except` to handle a target that is out of reach
- Write Lesson 7's gradient descent as code (`error`, `cost`, `slopes` and the `ik_gd` loop) and test different learning rates
- Run both methods on the same targets and explain why their answers can differ
- Describe what the Jacobian shows and why a Jacobian method needs fewer steps than gradient descent
- Find the steps of Lesson 6's recipe in the arm's own control code

## Files

| File | What it is |
|------|------------|
| [Lesson Plan 8 - Code Implementation of Inverse Kinematics and Other Methods.pdf](Lesson%20Plan%208%20-%20Code%20Implementation%20of%20Inverse%20Kinematics%20and%20Other%20Methods.pdf) | Lesson plan with timed procedures, worked answers and assessment |
| [Lesson Plan 8 - Code Implementation of Inverse Kinematics and Other Methods.docx](Lesson%20Plan%208%20-%20Code%20Implementation%20of%20Inverse%20Kinematics%20and%20Other%20Methods.docx) | Lesson plan (Word, editable) |
| [Lesson_8_Code_Implementation_of_IK.pdf](Lesson_8_Code_Implementation_of_IK.pdf) | Slides (PDF) |
| [Lesson_8_Code_Implementation_of_IK.pptx](Lesson_8_Code_Implementation_of_IK.pptx) | Slides (PowerPoint, editable) |

## The steps in code

**Day 1: Lesson 6's triangles**

1. `law_of_cosines(a, b, c)`: the angle opposite side c, from cos C = (a² + b² − c²) ÷ (2ab)
2. `elbow(D)`: θE = −(180° − γ), where γ is the angle inside the triangle at the elbow. Elbow up, so θE is negative.
3. `shoulder(X, Y, D)`: θS = φ + δ, with φ = atan2(Y, X)
4. `ik_flat(X, Y)`: D = √(X² + Y²). If D is more than 500 mm, it raises `ValueError("target is out of reach")`.
5. `ik_3d(x, y, z)`: θB = atan2(y, x) and R = √(x² + y²), then `ik_flat(R, z)` does the rest

**Day 2: Lesson 7's gradient descent**

6. `error` and `cost`: the distance from the FK tip to the target, and C = (error ÷ 250)²
7. `slopes`: nudge each joint up and down by h = 0.0001 rad and see how the cost changes
8. `ik_gd`: θ_new = θ − η × slope for each joint, until the error is under 0.5 mm or 1000 steps have run

For the worked example (301.78, 301.78, 176.78), `ik_3d` gives [45.0, 45.0, −45.0]. `ik_gd` gives [45.0, 45.15, −45.29] in 84 steps, 0.49 mm from the target, the same as the computer run in Lesson 7. The Jacobian method in `jacobian_preview.py` gets there in 5 steps.

## Code

The code for this lesson is in the [Code folder](../../Code/). It needs only Python 3. Keep the files in one folder with [`arm.py`](../../Code/arm.py) from Lesson 5, because they import it.

| Day | File | Who it's for | What to do with it |
|-----|------|--------------|--------------------|
| 1–2 | [`ik_starter.py`](../../Code/ik_starter.py) | Students | Save a copy as `ik.py` and add the functions one step at a time (Steps 1 to 8) |
| 1–2 | [`ik.py`](../../Code/ik.py) | Teacher | Solution: `law_of_cosines`, `elbow`, `shoulder`, `ik_flat`, `ik_3d`, `error`, `cost`, `slopes` and `ik_gd`. Hold it back until students have tried the steps themselves, because the same code is on the slides |
| 2 | [`check_ik.py`](../../Code/check_ik.py) | Students | Runs both methods on four targets from Lesson 6 and prints the table for "Test Both Methods" |
| 2 | [`jacobian_preview.py`](../../Code/jacobian_preview.py) | Students | Prints the Jacobian at (45°, 45°, −45°), then 5 steps (0.01 mm) for the Jacobian method and 84 steps (0.49 mm) for gradient descent. Students run it but do not need to write it |

Check your code with the worked example: running `ik.py` prints `[45.0, -45.0]`, `[45.0, 45.0, -45.0]`, `[45.0, 45.15, -45.29]` and `84 0.49`.

The code uses link lengths of L1 = L2 = 250 mm and the DH angles from Lessons 4 to 7: θB is the base turn, θS is measured from the floor, θE is measured from the line of the upper arm, and up is +. If your arm measures differently, change the two constants at the top of `arm.py`. The answers on the slides will change too. The `inverse_kinematics` function in [`waypoint.py`](../../Code/waypoint.py) follows the same steps, but it uses 220 mm links, metres and radians, and measures the shoulder from straight up.

**Previous:** [Lesson 7: Gradient Descent Approach to IK](../Lesson%207/) · **Next:** [Lesson 9: AI Object Detection](../Lesson%209/)

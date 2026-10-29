"""Lesson 8: inverse kinematics in Python.

The two methods from Lessons 6 and 7, written as code:
    Day 1  trigonometry: the law of cosines (Lesson 6)
    Day 2  gradient descent: guess, measure, improve (Lesson 7)

Angles are in degrees, measured the DH way, as in arm.py from Lesson 5:
    theta_b  the base turn, measured from the x axis
    theta_s  the upper arm, measured from the floor
    theta_e  the forearm, measured from the line of the upper arm
Up is +, so elbow up means theta_e is negative. Lengths are in mm.
Save this file in the same folder as arm.py.
"""
import math
from arm import L1, L2, show, flat_tip, tip_3d


# ---------- Day 1: trigonometry (Lesson 6) ----------

# Step 1
def law_of_cosines(a, b, c):
    """The angle (degrees) opposite side c in a triangle with sides a, b, c."""
    cos_c = (a ** 2 + b ** 2 - c ** 2) / (2 * a * b)
    cos_c = max(-1, min(1, cos_c))      # rounding can give 1.0000001
    return math.degrees(math.acos(cos_c))


# Step 2
def elbow(D):
    """The elbow angle theta_e for a target D mm away (elbow up)."""
    gamma = law_of_cosines(L1, L2, D)   # the angle inside the triangle
    return -(180 - gamma)               # the bend, down is negative


# Step 3
def shoulder(X, Y, D):
    """The shoulder angle theta_s for the target (X, Y) (elbow up)."""
    phi = math.degrees(math.atan2(Y, X))    # the tilt of the line D
    delta = law_of_cosines(L1, D, L2)       # between D and the upper arm
    return phi + delta


# Step 4
def ik_flat(X, Y):
    """The flat arm: target (X, Y) -> [theta_s, theta_e]."""
    D = math.sqrt(X ** 2 + Y ** 2)
    if D > L1 + L2:
        raise ValueError("target is out of reach")
    return [shoulder(X, Y, D), elbow(D)]


# Step 5
def ik_3d(x, y, z):
    """The 3D arm: target (x, y, z) -> [theta_b, theta_s, theta_e]."""
    theta_b = math.degrees(math.atan2(y, x))   # aim the base
    R = math.sqrt(x ** 2 + y ** 2)             # flatten: reach across the floor
    theta_s, theta_e = ik_flat(R, z)           # the flat arm does the rest
    return [theta_b, theta_s, theta_e]


# ---------- Day 2: gradient descent (Lesson 7) ----------
# The step rule uses radians, so inside the loop the angles are in radians.

# Step 6
def error(angles, target):
    """How far (mm) the tip is from the target. angles in radians."""
    degrees = [math.degrees(a) for a in angles]
    tip = tip_3d(*degrees)
    total = 0
    for i in range(3):
        total += (tip[i] - target[i]) ** 2
    return math.sqrt(total)


def cost(angles, target):
    """The cost from Lesson 7: C = (error / 250) ** 2."""
    return (error(angles, target) / L1) ** 2


# Step 7
def slopes(angles, target, h=0.0001):
    """One slope per joint: nudge that joint up and down by h radians."""
    result = []
    for i in range(3):
        up = list(angles)
        up[i] += h
        down = list(angles)
        down[i] -= h
        result.append((cost(up, target) - cost(down, target)) / (2 * h))
    return result


# Step 8
def ik_gd(target, start=(0, 45, -45), eta=0.1, tol=0.5, max_steps=1000):
    """Gradient descent IK. Returns the angles (degrees), the steps used
    and the error that is left (mm)."""
    angles = [math.radians(a) for a in start]
    steps = 0
    while steps < max_steps and error(angles, target) >= tol:
        g = slopes(angles, target)
        for i in range(3):
            angles[i] = angles[i] - eta * g[i]    # one step downhill
        steps += 1
    degrees = [math.degrees(a) for a in angles]
    return degrees, steps, error(angles, target)


if __name__ == "__main__":
    show(ik_flat(426.78, 176.78))                 # [45.0, -45.0]
    show(ik_3d(301.78, 301.78, 176.78))           # [45.0, 45.0, -45.0]
    angles, steps, err = ik_gd((301.78, 301.78, 176.78))
    show(angles)                                  # [45.0, 45.15, -45.29]
    print(steps, round(err, 2))                   # 84 0.49

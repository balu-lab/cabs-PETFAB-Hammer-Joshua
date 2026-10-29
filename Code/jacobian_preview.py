"""Lesson 8 preview: the Jacobian.

The Jacobian is a table that says how far the tip moves when each joint
turns by 1 degree. A Jacobian method uses that table to choose all three
joint changes at once, so it needs far fewer steps than gradient descent.
You do not need to write this code. Run it and compare the step counts.
Save it in the same folder as arm.py and ik.py.
"""
import math
from arm import show, tip_3d
from ik import ik_gd


def jacobian(angles, h=0.001):
    """One column per joint: how the tip (x, y, z) moves, in mm per degree."""
    tip = tip_3d(*angles)
    columns = []
    for i in range(3):
        nudged = list(angles)
        nudged[i] += h
        moved = tip_3d(*nudged)
        columns.append([(moved[k] - tip[k]) / h for k in range(3)])
    return columns


def det3(a, b, c):
    """A number made from three columns (the determinant). 0 means stuck."""
    return (a[0] * (b[1] * c[2] - b[2] * c[1])
            - b[0] * (a[1] * c[2] - a[2] * c[1])
            + c[0] * (a[1] * b[2] - a[2] * b[1]))


def solve(columns, move):
    """The joint changes (degrees) that move the tip by move."""
    a, b, c = columns
    d = det3(a, b, c)
    return [det3(move, b, c) / d, det3(a, move, c) / d, det3(a, b, move) / d]


def ik_jacobian(target, start=(0, 45, -45), tol=0.5, max_steps=100,
                max_turn=20):
    """Jacobian IK: each step aims the tip straight at the target."""
    angles = list(start)
    steps = 0
    while steps < max_steps:
        tip = tip_3d(*angles)
        move = [target[k] - tip[k] for k in range(3)]
        error = math.sqrt(move[0] ** 2 + move[1] ** 2 + move[2] ** 2)
        if error < tol:
            break
        change = solve(jacobian(angles), move)
        biggest = max(abs(c) for c in change)
        if biggest > max_turn:              # never turn a joint too far at once
            change = [c * max_turn / biggest for c in change]
        for i in range(3):
            angles[i] += change[i]
        steps += 1
    return angles, steps, error


if __name__ == "__main__":
    for column in jacobian([45, 45, -45]):
        show(column)            # how the tip moves per degree of each joint

    target = (301.78, 301.78, 176.78)
    angles, steps, err = ik_jacobian(target)
    show(angles)
    print("Jacobian:", steps, "steps,", round(err, 2), "mm")
    angles, steps, err = ik_gd(target)
    print("gradient descent:", steps, "steps,", round(err, 2), "mm")

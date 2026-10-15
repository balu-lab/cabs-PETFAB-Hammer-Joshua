"""Lesson 5, Day 1 starter: forward kinematics in code.

Angles are in degrees. Lengths are in mm.
Save a copy of this file as fk.py, fill in the two functions marked TODO,
then run:  python fk.py
"""
import numpy as np

L1 = 250   # upper arm length (mm)
L2 = 250   # forearm length (mm)


def show(p):
    """Print a position rounded to 2 decimals (and never -0.0)."""
    print([round(float(v), 2) + 0.0 for v in p])


def dh_matrix(theta, d, a, alpha):
    """Return the 4x4 DH matrix for one joint.

    theta and alpha are in degrees. d and a are in mm.
    """
    # TODO 1: turn theta and alpha into radians (np.radians)
    # TODO 2: work out cos and sin of each (short names ct, st, ca, sa help)
    # TODO 3: return the 4x4 matrix from Lesson 4, slide 22, as an np.array
    pass


def forward_kinematics(theta_b, theta_s, theta_e):
    """Return the tip position (x, y, z) in mm for the three joint angles."""
    # TODO 4: build A1, A2, A3 from the DH table (one dh_matrix call per row)
    # TODO 5: multiply them in joint order with @
    # TODO 6: return the last column of T (first three numbers)
    pass


if __name__ == "__main__":
    tip = forward_kinematics(45, 45, 45)
    show(tip)   # should print [301.78, 301.78, 176.78]

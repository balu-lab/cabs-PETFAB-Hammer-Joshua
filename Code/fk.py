"""Lesson 5, Day 1 solution: forward kinematics in code.

Angles are in degrees. Lengths are in mm.
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
    t = np.radians(theta)
    al = np.radians(alpha)
    ct, st = np.cos(t), np.sin(t)
    ca, sa = np.cos(al), np.sin(al)
    return np.array([
        [ct, -st * ca, st * sa, a * ct],
        [st, ct * ca, -ct * sa, a * st],
        [0, sa, ca, d],
        [0, 0, 0, 1],
    ])


def forward_kinematics(theta_b, theta_s, theta_e):
    """Return the tip position (x, y, z) in mm for the three joint angles."""
    A1 = dh_matrix(theta_b, 0, 0, 90)           # base
    A2 = dh_matrix(90 - theta_s, 0, L1, 0)      # shoulder
    A3 = dh_matrix(-theta_e, 0, L2, 0)          # elbow
    T = A1 @ A2 @ A3
    return T[:3, 3]


if __name__ == "__main__":
    tip = forward_kinematics(45, 45, 45)
    show(tip)   # prints [301.78, 301.78, 176.78]

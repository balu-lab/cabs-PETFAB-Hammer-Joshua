"""Helper functions for Lesson 5, Day 2: forward kinematics with screw theory.

Angles are in degrees. Lengths are in mm.
"""
import numpy as np


def skew(w):
    """3x3 matrix that does a cross product: skew(w) @ v equals np.cross(w, v)."""
    return np.array([[0, -w[2], w[1]],
                     [w[2], 0, -w[0]],
                     [-w[1], w[0], 0]])


def screw_axis(direction, point):
    """Describe a turning joint: which way its axis points and one point on the axis.

    Returns the 6 numbers (wx, wy, wz, vx, vy, vz) of the joint's screw axis.
    """
    w = np.array(direction, dtype=float)
    w = w / np.linalg.norm(w)               # make the direction length 1
    v = -np.cross(w, np.array(point, dtype=float)) + 0.0   # + 0.0 turns -0.0 into 0.0
    return np.concatenate([w, v])


def screw_matrix(S, theta):
    """4x4 matrix for turning a joint with screw axis S by theta degrees."""
    w, v = np.array(S[:3]), np.array(S[3:])
    t = np.radians(theta)
    W = skew(w)
    R = np.eye(3) + np.sin(t) * W + (1 - np.cos(t)) * (W @ W)
    p = (np.eye(3) * t + (1 - np.cos(t)) * W + (t - np.sin(t)) * (W @ W)) @ v
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = p
    return T

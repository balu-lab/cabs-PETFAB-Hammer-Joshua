"""Lesson 5, Day 2 solution: forward kinematics with screw theory."""
import numpy as np
from screw_helper import screw_axis, screw_matrix

L1 = 250   # upper arm length (mm)
L2 = 250   # forearm length (mm)

# Home pose: every angle 0, arm straight up. The tip is at (0, 0, L1 + L2).
M = np.array([[1, 0, 0, 0],
              [0, 1, 0, 0],
              [0, 0, 1, L1 + L2],
              [0, 0, 0, 1]])

S1 = screw_axis([0, 0, 1], [0, 0, 0])    # base: turns about z, through the origin
S2 = screw_axis([0, 1, 0], [0, 0, 0])    # shoulder: turns about y, through the origin
S3 = screw_axis([0, 1, 0], [0, 0, L1])   # elbow: turns about y, through (0, 0, L1)


def forward_kinematics_screw(theta_b, theta_s, theta_e):
    """Return the tip position (x, y, z) in mm, using screw theory."""
    T = (screw_matrix(S1, theta_b)
         @ screw_matrix(S2, theta_s)
         @ screw_matrix(S3, theta_e)
         @ M)
    return T[:3, 3]


if __name__ == "__main__":
    print([round(float(v), 2) + 0.0 for v in forward_kinematics_screw(45, 45, 45)])

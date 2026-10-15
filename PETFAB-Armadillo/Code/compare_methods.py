"""Lesson 5, Day 2: compare the DH function with Lesson 3's trigonometry.

Put this file next to fk.py and run:  python compare_methods.py
"""
import random
import numpy as np
from fk import forward_kinematics as fk, L1, L2


def trig_fk(theta_b, theta_s, theta_e):
    b = np.radians(theta_b)
    s = np.radians(theta_s)
    se = np.radians(theta_s + theta_e)
    r = L1 * np.sin(s) + L2 * np.sin(se)
    z = L1 * np.cos(s) + L2 * np.cos(se)
    return np.array([r * np.cos(b), r * np.sin(b), z])


worst = 0
for _ in range(2000):
    angles = [random.uniform(-180, 180) for _ in range(3)]
    diff = np.abs(fk(*angles) - trig_fk(*angles)).max()
    worst = max(worst, diff)

print(worst < 0.000001)

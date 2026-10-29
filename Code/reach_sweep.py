"""Lesson 5, Day 2: try many poses and see how far the tip can be from the base.

Put this file next to arm.py and run:  python reach_sweep.py
"""
import math
from arm import flat_tip

distances = []
for theta_s in range(0, 91, 10):          # shoulder: 0 to 90 degrees
    for theta_e in range(-90, 1, 10):     # elbow: -90 to 0 degrees (bending down)
        x, z = flat_tip(theta_s, theta_e)
        distances.append(math.sqrt(x ** 2 + z ** 2))

print(len(distances), "poses")
print("farthest:", round(max(distances), 2), "mm")
print("nearest:", round(min(distances), 2), "mm")

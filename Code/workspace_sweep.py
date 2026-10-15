"""Lesson 5, Day 2: sweep the joint angles and plot where the arm's tip can reach.

Run:  python workspace_sweep.py      (needs matplotlib:  pip install matplotlib)
"""
import numpy as np
import matplotlib.pyplot as plt
from fk import forward_kinematics as fk

points = []
for theta_s in range(0, 91, 5):        # shoulder: 0 to 90 degrees, in steps of 5
    for theta_e in range(0, 91, 5):    # elbow: 0 to 90 degrees, in steps of 5
        x, y, z = fk(0, theta_s, theta_e)   # base angle 0: side view
        points.append((x, z))

points = np.array(points)
reach = np.hypot(points[:, 0], points[:, 1])   # distance from the shoulder

print(len(points), "poses")
print("farthest:", round(reach.max(), 2), "mm")
print("nearest:", round(reach.min(), 2), "mm")

plt.scatter(points[:, 0], points[:, 1])
plt.axis("equal")
plt.xlabel("x (mm)")
plt.ylabel("z (mm)")
plt.show()

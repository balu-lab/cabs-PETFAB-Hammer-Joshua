"""Lesson 5, Day 2 (optional): plot the tip for each pose.

Needs matplotlib:  pip install matplotlib
Put this file next to arm.py and run:  python reach_plot.py
"""
import matplotlib.pyplot as plt
from arm import flat_tip

xs = []
zs = []
for theta_s in range(0, 91, 10):
    for theta_e in range(-90, 1, 10):
        x, z = flat_tip(theta_s, theta_e)
        xs.append(x)
        zs.append(z)

plt.scatter(xs, zs)
plt.axis("equal")
plt.xlabel("across (mm)")
plt.ylabel("up (mm)")
plt.show()

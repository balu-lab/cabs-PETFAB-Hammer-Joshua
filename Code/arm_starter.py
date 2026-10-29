"""Lesson 5 starter file.

Save a copy of this file as arm.py. We add to it, one step at a time.
Angles are in degrees, measured the DH way (up is +, down is -).
Lengths are in mm.
"""
import math

L1 = 250   # upper arm length (mm)
L2 = 250   # forearm length (mm)


def show(v):
    """Print a vector with each number rounded to 2 decimals."""
    print([round(n, 2) + 0.0 for n in v])   # + 0.0 stops it printing -0.0


# Day 1
# Step 1: write arrow(theta)
# Step 2: write scale(k, v) and add_vectors(u, v)
# Step 3: write turn_90(v) and turn(e, n, theta)
# Step 4: write flat_tip(theta_s, theta_e)

# Day 2
# Step 5: write arrow_3d(theta_b, theta_s) and turned_3d(theta_b, theta_s)
# Step 6: write tip_3d(theta_b, theta_s, theta_e)
# Lesson 3's method: write trig_tip(theta1, theta2, theta3)

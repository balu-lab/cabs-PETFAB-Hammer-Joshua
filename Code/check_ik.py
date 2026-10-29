"""Lesson 8, Day 2: test both IK methods on the same targets.

Put this file next to arm.py and ik.py and run:  python check_ik.py
"""
from arm import show, tip_3d
from ik import ik_3d, ik_gd

targets = [(301.78, 301.78, 176.78),     # the worked example
           (295.75, 170.75, 91.51),      # Lesson 6, Try It Yourself #4
           (-324.76, 187.50, 216.51),    # Lesson 6, Try It Yourself #5
           (400, 300, 200)]              # out of reach

for target in targets:
    print("target:", target)
    try:
        angles = ik_3d(*target)
        print("  trig:", end=" ")
        show(angles)
    except ValueError:
        print("  trig: out of reach")
    angles, steps, err = ik_gd(target)
    print("  gd:  ", end=" ")
    show(angles)
    print("        ", steps, "steps, error", round(err, 2), "mm")

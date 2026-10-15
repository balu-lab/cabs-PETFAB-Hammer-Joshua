"""Lesson 5: a pass/fail test for forward_kinematics.

Put this file next to fk.py and run:  python check_fk.py
To test another version, change the import line (line 8).
The expected answers assume L1 = L2 = 250 mm.
"""
import numpy as np
from fk import forward_kinematics as fk

# (theta_b, theta_s, theta_e) -> expected tip (x, y, z) in mm
TESTS = [
    ((0, 0, 0),     (0.00, 0.00, 500.00)),       # arm straight up
    ((90, 0, 0),    (0.00, 0.00, 500.00)),       # base turns, tip stays on the axis
    ((0, 90, 0),    (500.00, 0.00, 0.00)),       # arm straight out along x
    ((90, 90, 0),   (0.00, 500.00, 0.00)),       # arm straight out along y
    ((45, 45, 45),  (301.78, 301.78, 176.78)),   # worked example, Lessons 3 and 4
    ((30, 60, 0),   (375.00, 216.51, 250.00)),   # Lesson 4, Try It Yourself #4
    ((120, 0, 90),  (-125.00, 216.51, 250.00)),  # Lesson 4, Try It Yourself #5
]

passed = 0
for angles, expected in TESTS:
    got = fk(*angles)
    ok = np.allclose(got, expected, atol=0.01)   # allow for rounding
    passed += ok
    shown = [round(float(v), 2) + 0.0 for v in got]
    print("PASS" if ok else "FAIL", angles, "->", shown, "expected", list(expected))

print(passed, "of", len(TESTS), "tests passed")

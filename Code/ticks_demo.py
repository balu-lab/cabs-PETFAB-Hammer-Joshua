"""Lesson 5 (optional): turn motor ticks into degrees.

The servos count 4096 ticks for one full turn.
ZERO_TICKS is the reading when the joint is at 0 degrees.
2048 is a placeholder: measure the real value on the built arm.
If a motor counts the other way, change the sign (in the DH convention, up is +).
"""
TICKS_PER_TURN = 4096
ZERO_TICKS = 2048


def ticks_to_degrees(ticks, gear_ratio=1):
    turns = (ticks - ZERO_TICKS) / TICKS_PER_TURN
    return turns * 360 / gear_ratio


print(ticks_to_degrees(2560))                        # shoulder or elbow: 45.0
print(ticks_to_degrees(2048 + 1536, gear_ratio=3))   # base, geared 3 to 1: 45.0

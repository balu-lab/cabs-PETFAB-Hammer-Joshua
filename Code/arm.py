"""Lesson 5: forward kinematics in Python, with the DH steps from Lesson 4.

Angles are in degrees, measured the DH way (up is +, down is -):
    theta_s  the upper arm, measured from the floor
    theta_e  the forearm, measured from the line of the upper arm
    theta_b  the base turn, measured from the x axis
Lengths are in mm.
"""
import math

L1 = 250   # upper arm length (mm)
L2 = 250   # forearm length (mm)


def show(v):
    """Print a vector with each number rounded to 2 decimals."""
    print([round(n, 2) + 0.0 for n in v])   # + 0.0 stops it printing -0.0


# ---------- Day 1: the flat arm ----------

# Step 1
def arrow(theta):
    """The unit vector (length 1) at angle theta from the floor."""
    theta = math.radians(theta)
    return [math.cos(theta), math.sin(theta)]


# Step 2
def scale(k, v):
    """Multiply every number in v by k."""
    result = []
    for i in range(len(v)):
        result.append(k * v[i])
    return result


def add_vectors(u, v):
    """Add two vectors that have the same number of entries."""
    result = []
    for i in range(len(u)):
        result.append(u[i] + v[i])
    return result


# Step 3
def turn_90(v):
    """Turn a flat vector 90 degrees counterclockwise: (x, y) -> (-y, x)."""
    return [-v[1], v[0]]


def turn(e, n, theta):
    """Turn the arrow e by theta, toward n: cos(theta) e + sin(theta) n."""
    theta = math.radians(theta)
    a = scale(math.cos(theta), e)
    b = scale(math.sin(theta), n)
    return add_vectors(a, b)


# Step 4
def flat_tip(theta_s, theta_e):
    """The tip [x, z] of the flat arm: L1 e + L2 f."""
    e = arrow(theta_s)          # the upper arm's arrow
    n = turn_90(e)              # e turned 90 degrees
    f = turn(e, n, theta_e)     # the forearm's arrow
    return add_vectors(scale(L1, e), scale(L2, f))


# ---------- Day 2: add the base turn ----------

# Step 5
def arrow_3d(theta_b, theta_s):
    """The upper arm's arrow e in 3D."""
    b = math.radians(theta_b)
    s = math.radians(theta_s)
    x = math.cos(s) * math.cos(b)
    y = math.cos(s) * math.sin(b)
    z = math.sin(s)
    return [x, y, z]


def turned_3d(theta_b, theta_s):
    """n in 3D: e turned 90 degrees up. It is e with theta_s + 90."""
    return arrow_3d(theta_b, theta_s + 90)


# Step 6
def tip_3d(theta_b, theta_s, theta_e):
    """The tip [x, y, z] of the arm: the same steps as flat_tip."""
    e = arrow_3d(theta_b, theta_s)
    n = turned_3d(theta_b, theta_s)
    f = turn(e, n, theta_e)
    return add_vectors(scale(L1, e), scale(L2, f))


# ---------- Lesson 3's method, in code ----------

def trig_tip(theta1, theta2, theta3):
    """Lesson 3's method, with Lesson 3's angles.

    theta1: the upper arm, measured from straight up
    theta2: the elbow bend, measured from the line of the upper arm
    theta3: the base turn
    """
    a1 = math.radians(theta1)
    a2 = math.radians(theta1 + theta2)
    b = math.radians(theta3)
    r = L1 * math.sin(a1) + L2 * math.sin(a2)   # the reach
    z = L1 * math.cos(a1) + L2 * math.cos(a2)   # the height (Lesson 3 called it Y)
    x = r * math.cos(b)
    y = r * math.sin(b)
    return [x, y, z]


if __name__ == "__main__":
    show(flat_tip(45, -45))       # [426.78, 176.78]
    show(tip_3d(45, 45, -45))     # [301.78, 301.78, 176.78]

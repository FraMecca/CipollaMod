import math

from cube2common.constants import RAD
from cube2common.vec import vec


def vecfromyawpitch(yaw, pitch, move, strafe):
    m = vec(0, 0, 0)
    if move:
        m.x = move * -math.sin(RAD * yaw)
        m.y = move * math.cos(RAD * yaw)
    else:
        m.x = m.y = 0

    if pitch:
        m.x *= math.cos(RAD * pitch)
        m.y *= math.cos(RAD * pitch)
        m.z = move * math.sin(RAD * pitch)
    else:
        m.z = 0

    if strafe:
        m.x += strafe * math.cos(RAD * yaw)
        m.y += strafe * math.sin(RAD * yaw)

    return m

from cube2common.utils.clamp import clamp
from cube2common.utils.vecfromyawpitch import vecfromyawpitch
from cube2common.vec import vec
from cube2protocol.sauerbraten.collect.physics_state import PhysicsState


def read_physics_state(cds):
    d = PhysicsState()

    physstate = cds.getbyte()
    flags = cds.getuint()

    for k in range(3):
        n = cds.getbyte()
        n |= cds.getbyte() << 8
        if flags & (1 << k):
            n |= cds.getbyte() << 16
            if n & 0x800000:
                n |= -1 << 24
        d.o[k] = n

    dir = cds.getbyte()
    dir |= cds.getbyte() << 8
    yaw = dir % 360
    pitch = clamp(dir / 360, 0, 180) - 90
    roll = clamp(int(cds.getbyte()), 0, 180) - 90
    mag = cds.getbyte()
    if flags & (1 << 3):
        mag |= cds.getbyte() << 8
    dir = cds.getbyte()
    dir |= cds.getbyte() << 8

    d.vel = vecfromyawpitch(dir % 360, clamp(dir / 360, 0, 180) - 90, 1, 0);

    if flags & (1 << 4):
        mag = cds.getbyte()
        if flags & (1 << 5):
            mag |= cds.getbyte() << 8

        if flags & (1 << 6):
            dir = cds.getbyte()
            dir |= cds.getbyte() << 8
            falling = vecfromyawpitch(dir % 360, clamp(dir / 360, 0, 180) - 90, 1, 0)
        else:
            falling = vec(0, 0, -1)
    else:
        falling = vec(0, 0, 0)

    d.falling = falling

    seqcolor = (physstate >> 3) & 1

    d.yaw = yaw
    d.pitch = pitch
    d.roll = roll

    if (physstate >> 4) & 2:
        d.move = -1
    else:
        d.move = (physstate >> 4) & 1

    if (physstate >> 6) & 2:
        d.strafe = -1
    else:
        d.strafe = (physstate >> 6) & 1

    d.physstate = physstate & 7

    return d

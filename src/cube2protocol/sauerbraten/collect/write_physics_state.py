from cube2common.constants import DVELF, material_types, empty_material_types
from cube2common.ivec import ivec
from cube2common.utils.clamp import clamp
from cube2common.utils.vectoyawpitch import vectoyawpitch
from cube2common.vec import vec


def dummy_air_material_lookup(position):
    "You actually need the map oct-tree data to determine what material is at a particular position."
    return empty_material_types.MAT_AIR

def write_physics_state(cds, physics_state):
    d = physics_state

    # TODO: replace this with an actual lookup for which material is at a particular position
    lookupmaterial = dummy_air_material_lookup

    # 3 bits phys state, 1 bit life sequence, 2 bits move, 2 bits strafe
    physstate = d.physstate | ((d.lifesequence & 1) << 3) | ((d.move & 3) << 4) | ((d.strafe & 3) << 6)
    cds.putbyte(physstate)
    o = ivec(vec(d.o.x, d.o.y, d.o.z - d.eyeheight))

    vel = min(int(d.vel.magnitude() * DVELF), 0xFFFF)
    fall = min(int(d.falling.magnitude() * DVELF), 0xFFFF)

    # 3 bits position, 1 bit velocity, 3 bits falling, 1 bit material
    flags = 0;
    if (o.x < 0 or o.x > 0xFFFF): flags |= 1 << 0
    if (o.y < 0 or o.y > 0xFFFF): flags |= 1 << 1
    if (o.z < 0 or o.z > 0xFFFF): flags |= 1 << 2
    if (vel > 0xFF): flags |= 1 << 3

    if fall > 0:
        flags |= 1 << 4
        if fall > 0xFF:
            flags |= 1 << 5
        if d.falling.x or d.falling.y or d.falling.z > 0:
            flags |= 1 << 6

    if lookupmaterial(d.feetpos()) & material_types.MATF_CLIP == empty_material_types.MAT_GAMECLIP:
        flags |= 1 << 7

    cds.putuint(flags)
    for k in range(3):
        cds.putbyte(o[k] & 0xFF)
        cds.putbyte((o[k] >> 8) & 0xFF)
        if o[k] < 0 or o[k] > 0xFFFF:
            cds.putbyte((o[k] >> 16) & 0xFF)


    if d.yaw < 0:
        dir = 360 + int(d.yaw) % 360
    else:
        dir = int(d.yaw) % 360

    dir += clamp(int(d.pitch + 90), 0, 180) * 360

    cds.putbyte(dir & 0xFF)
    cds.putbyte((dir >> 8) & 0xFF)
    cds.putbyte(clamp(int(d.roll + 90), 0, 180))
    cds.putbyte(vel & 0xFF)
    if vel > 0xFF:
        cds.putbyte((vel >> 8) & 0xFF)

    velyaw, velpitch = vectoyawpitch(d.vel)

    if velyaw < 0:
        veldir = 360 + int(velyaw) % 360
    else:
        veldir = int(velyaw) % 360

    veldir += clamp(int(velpitch + 90), 0, 180) * 360

    cds.putbyte(veldir & 0xFF)
    cds.putbyte((veldir >> 8) & 0xFF)

    if fall > 0:
        cds.putbyte(fall & 0xFF)

        if fall > 0xFF:
            cds.putbyte((fall >> 8) & 0xFF)

        if d.falling.x or d.falling.y or d.falling.z > 0:
            fallyaw, fallpitch = vectoyawpitch(d.falling)

            if fallyaw < 0:
                falldir = 360 + int(fallyaw) % 360
            else:
                falldir = int(fallyaw) % 360

            falldir += clamp(int(fallpitch + 90), 0, 180) * 360

            cds.putbyte(falldir & 0xFF)
            cds.putbyte((falldir >> 8) & 0xFF)

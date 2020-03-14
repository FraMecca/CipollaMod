from cube2common.vec import vec

class PhysicsState(object):
    def __init__(self):
        self.physstate = 0
        self.lifesequence = 0
        self.move = 0
        self.yaw = 0
        self.roll = 0
        self.pitch = 0
        self.strafe = 0

        self.o = vec(0, 0, 0)

        self.falling = vec(0, 0, 0)
        self.eyeheight = 14
        self.vel = vec(0, 0, 0)
        
    def feetpos(self):
        return vec(0, 0, -self.eyeheight).add(self.o)
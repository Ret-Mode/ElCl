import arcade
import pymunk

# PyCharm type helper
from typing import Optional, Dict, List, Tuple, Any

import util
import math


class Keys:
    def __init__(self):
        self.k = {arcade.key.W: False,
                  arcade.key.S: False,
                  arcade.key.A: False,
                  arcade.key.D: False,
                  arcade.key.E: False,
                  arcade.key.SPACE: False
                  }

    def setKey(self, key):
        self.k[key] = True

    def unsetKey(self, key):
        self.k[key] = False


class Level:

    def __init__(self):
        self.bd: Dict[pymunk.Body] = {}
        self.shp: Dict[pymunk.Shape] = {}
        self.cns: Dict[pymunk.Constraint] = {}
        self.type: str = "level"
        self.player_x = 300
        self.player_y = 300
        self.enemiesToLoad = []

    def remove(self, space):
        for v in self.cns:
            space.remove(self.cns[v])
        for v in self.shp:
            space.remove(self.shp[v])
        for v in self.bd:
            space.remove(self.bd[v])

    def create(self, space):
        pass

    def draw(self, drawVectors=True, drawGraphics=True, filter=None):

        if drawVectors:
            util.drawVectors(self.shp)


# autogeometry level
# TODO [EH] join it with Level Class
class Level2:

    def __init__(self):
        self.bd: Dict[pymunk.Body] = {}
        self.shp: Dict[pymunk.Shape] = {}
        self.cns: Dict[pymunk.Constraint] = {}
        self.type = "autogeometry"
        self.t: Optional[arcade.sprite.Sprite] = None

        self.enemiesToLoad = []
        self.segments = []
        self.autogeometry_dx = 60
        self.autogeometry_dy = 60
        self.scale = 2.0
        self.alpha_threshold = 0.5
        self.friction = 5
        self.elasticity = 0.0
        self.player_x = 300
        self.player_y = 300

    def remove(self, space):
        for v in self.cns:
            space.remove(self.cns[v])
        for v in self.shp:
            space.remove(self.shp[v])
        for v in self.bd:
            space.remove(self.bd[v])
        self.t.kill()
        self.t = None

    def create(self, space):
        # TODO [EH] can it be removed?
        self.getMarchingCubes(self.autogeometry_dx, self.autogeometry_dy).sendSegmentsToPhysics(space)

    def getTexture(self, path):
        self.t = arcade.load_texture(path)
        return self

    def getMarchingCubes(self, autogeometry_dx: int, autogeometry_dy: int):
        def segment_func(v0, v1):
            seg = (((v0[0] * self.scale, v0[1] * self.scale),
                   (v1[0] * self.scale, v1[1] * self.scale),),)
            self.segments.append(seg)

        def sample_func(point):
            x = int(point.x)
            y = self.t.texture.height - 1 - int(point.y)
            return self.t.texture.image.getpixel((x, y))[3] / 255

        # TODO [EH] - add parameter whether march_soft or march_hard will be performed
        pymunk.autogeometry.march_soft(pymunk.BB(0, 0, self.t.texture.width-1, self.t.texture.height-1), autogeometry_dx, autogeometry_dy,
                                       self.alpha_threshold, segment_func, sample_func)

        return self

    def sendSegmentsToPhysics(self, space):
        # TODO [EH] change this body id into smthng else ?:P
        # TODO [EH] Should it be dumped to xml with texture setup?
        self.bd['new'] = pymunk.Body(1.0, 1.0, pymunk.Body.STATIC)
        space.add(self.bd['new'])
        s_id = 1
        for elems in range(len(self.segments)):
            for i in self.segments[elems]:
                sName = str(i) + '_' + str(s_id)
                self.shp[sName] = pymunk.Segment(self.bd['new'], i[0], i[1], 1)
                space.add(self.shp[sName])
                self.shp[sName].friction = self.friction
                self.shp[sName].elasticity = self.elasticity

    def draw(self, drawVectors=True, drawGraphics=True, filter=None):
        if drawGraphics:
            # TODO [EH] how to scale for nearest neighbour?
            #arcade.draw_scaled_texture_rectangle(self.t.width*self.scale/2, self.t.height*self.scale/2, self.t, self.scale)
            self.t._sprite_list._texture.filter = filter
            self.t.draw()
            pass
        if drawVectors:
            # TODO [EH] change to segment query directly from space or sorting, no it iterates everything
            viewport = arcade.get_viewport()
            for i in self.segments:
                for j in i:
                    if not ((j[0][0] < viewport[0] and j[1][0] < viewport[0]) or
                            (j[0][0] > viewport[1] and j[1][0] > viewport[1])) and not ((j[0][1] < viewport[2] and j[1][1] < viewport[2]) or
                                                                                    (j[0][1] > viewport[3] and j[1][1] > viewport[3])):
                        arcade.draw_line(j[0][0], j[0][1], j[1][0], j[1][1], arcade.color.LEMON, 1)


class Enemy:
    def __init__(self):
        self.bd: Dict[pymunk.Body] = {}
        self.shp: Dict[pymunk.Shape] = {}
        self.cns: Dict[pymunk.Constraint] = {}
        self.bdTex: Dict[arcade.sprite.Sprite] = {}
        self.type: str = "enemy"
        self.dir = -1
        self.hp = 1

    def flip(self):
        for n in self.bdTex:
            if self.bdTex[n].texture_rotation:
                self.bdTex[n].texture_transform.scale(-1, 1)

    def create(self, space):
        if self.dir < 0:
            self.flip()
            self.dir = 1

    def moveTo(self, x, y):
        for i in self.bd:
            self.bd[i].position += (x, y)

    def remove(self, space):
        for v in self.cns:
            space.remove(self.cns[v])
        for v in self.shp:
            space.remove(self.shp[v])
        for v in self.bd:
            space.remove(self.bd[v])
        for v in self.bdTex:
            self.bdTex[v].kill()

    def draw(self, drawVectors=True, drawGraphics=True, filter=None):

        if drawGraphics:
            for body in sorted(self.bd.keys()):
                self.bdTex[body].set_position(self.bd[body].position.x, self.bd[body].position.y)
                self.bdTex[body].angle = self.bd[body].angle * 180 / math.pi
                self.bdTex[body]._sprite_list._texture.filter = filter
                self.bdTex[body].draw()

        if drawVectors:
            util.drawVectors(self.shp)


class Vehicle:

    # TODO [EH] change this class into Vehicle

    def __init__(self):
        self.bd = {}
        self.shp = {}
        self.cns = {}
        self.bdTex: Dict[arcade.sprite.Sprite] = {}
        self.dir = 1  # TODO [EH] create some normal directions, now 1 is left wheel, -1 is right wheel
        self.postFlipAngleUpdate = 0.0
        self.prevDir = 1
        self.differential = False
        self.differentialDest = {}
        self.speed = 20
        self.startAngle = 0.0
        self.rotational_force = 20
        self.rotational_limit = 2
        self.centralId = ""
        self.motorParams = {}

    def remove(self, space):
        for v in self.cns:
            space.remove(self.cns[v])
        for v in self.shp:
            space.remove(self.shp[v])
        for v in self.bd:
            space.remove(self.bd[v])
        for v in self.bdTex:
            self.bdTex[v].kill()

    def create(self, space):
        #xml_parser.readData(path, space)
        #PhysicsDumper('car_2.xml', EXEC_FOLDER).dumpData(self)
        if self.dir < 0:
            self.flip()
            self.dir = 1

    def flip(self):
        for n in self.bdTex:
            if self.bdTex[n].texture_rotation:
                # TODO [EH] change to sprite flipping, not whole texture
                # TODO [EH] ... but weirdly sprite got one scale :D
                self.bdTex[n].texture_transform.scale(-1, 1)

        # reset acceleration of every motor wheel
        for motorId in self.motorParams:
            self.motorParams[motorId][2] = 0.0

        self.postFlipAngleUpdate = self.bd[self.centralId].angular_velocity

        util.flipConstraints(self.cns, self.bd[self.centralId], -self.startAngle * self.dir)
        # self.postFlipAngleUpdate = self.bd[self.centralId].angular_velocity
        # TODO [EH] Swap constraints and bodies

    def moveTo(self, x, y):
        for i in self.bd:
            self.bd[i].position += (x, y)

    def draw(self, drawVectors=True, drawGraphics=True, filter=None):

        if drawGraphics:
            for body in sorted(self.bd.keys()):
                self.bdTex[body].set_position(self.bd[body].position.x, self.bd[body].position.y)
                self.bdTex[body].angle = self.bd[body].angle * 180 / math.pi
                self.bdTex[body]._sprite_list._texture.filter = filter
                self.bdTex[body].draw()

        if drawVectors:
            util.drawVectors(self.shp)

    def update(self, key = None):

        # if self.postFlipAngleUpdate != 0.0:
        #     self.bd[self.centralId].angular_velocity += self.postFlipAngleUpdate
        #     self.postFlipAngleUpdate /= 1.5
        #     if 0.01 > self.postFlipAngleUpdate > -0.01:
        #         self.postFlipAngleUpdate = 0.0

        if key:
            if key.k[arcade.key.E]:
                self.differential = not self.differential
                key.unsetKey(arcade.key.E)

            # TODO [EH] this could be speed up for sure
            if key.k[arcade.key.W]:
                if self.dir > 0:
                    for motorId in self.motorParams:
                        motor = self.motorParams[motorId]
                        motor[2] = max(motor[2] - motor[1], -motor[0])
                        self.bd[motorId].angular_velocity = max(self.bd[motorId].angular_velocity + motor[2], -motor[0])
                else:
                    for motorId in self.motorParams:
                        motor = self.motorParams[motorId]
                        motor[2] = min(motor[2] + motor[1], motor[0])
                        self.bd[motorId].angular_velocity = min(self.bd[motorId].angular_velocity + motor[2], motor[0])

            elif key.k[arcade.key.S]:
                if self.dir > 0:
                    for motorId in self.motorParams:
                        motor = self.motorParams[motorId]
                        motor[2] = min(motor[2] + motor[1]/2, motor[0]/2)
                        self.bd[motorId].angular_velocity = min(self.bd[motorId].angular_velocity + motor[2]/2, motor[0]/2)
                else:
                    for motorId in self.motorParams:
                        motor = self.motorParams[motorId]
                        motor[2] = max(motor[2] - motor[1]/2, - motor[0]/2)
                        self.bd[motorId].angular_velocity = max(self.bd[motorId].angular_velocity + motor[2] / 2,
                                                                -motor[0] / 2)

            else:
                for motorId in self.motorParams:
                    self.motorParams[motorId][2] = 0.0

            if self.differential:
                for src in self.differentialDest:
                    for dest in self.differentialDest[src]:
                        self.bd[dest].angular_velocity = self.bd[src].angular_velocity

            if key.k[arcade.key.D] and self.bd[self.centralId].angular_velocity > -self.rotational_limit:

                self.bd[self.centralId].apply_impulse_at_local_point((self.rotational_force, 0), (0, 30))
                self.bd[self.centralId].apply_impulse_at_local_point((-self.rotational_force, 0), (0, -30))

            if key.k[arcade.key.A] and self.bd[self.centralId].angular_velocity < self.rotational_limit:

                self.bd[self.centralId].apply_impulse_at_local_point((-self.rotational_force, 0), (0, 30))
                self.bd[self.centralId].apply_impulse_at_local_point((self.rotational_force, 0), (0, -30))

            if key.k[arcade.key.SPACE]:
                self.dir *= -1
                self.flip()
                self.prevDir = self.dir
            key.unsetKey(arcade.key.SPACE)

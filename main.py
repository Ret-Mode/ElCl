"""
The GAME
"""
import os
import sys
import math
import time
import pyglet
import arcade
import pymunk

from typing import Optional  # TODO [EH] wut is this??????
import xml.etree.ElementTree as ET

# TODO [EH] shall it stay global? Move it into direct call?
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Platformer"

EXEC_FOLDER = os.getcwd()


class Level2:

    def __init__(self):
        self.bd = {}
        self.shp = {}
        self.cns = {}
        self.type = "png"
        self.t: Optional[arcade.Texture] = None
        self.segments = []
        self.density_x = 0
        self.density_y = 0
        self.scale_x = 2.0
        self.scale_y = 2.0
        self.alpha_threshold = 0.5

    def remove(self, space):
        for v in self.cns:
            space.remove(self.cns[v])
        for v in self.shp:
            space.remove(self.shp[v])
        for v in self.bd:
            space.remove(self.bd[v])

    def create(self, space):
        self.getTexture(EXEC_FOLDER + '\\mapa.png').getMarchingCubes(60, 60).sendSegmentsToPhysics(space)
        #PhysicsDumper('_level.xml', EXEC_FOLDER).readData(self, space)

    def getTexture(self, path):
        self.t = arcade.load_texture(path)
        return self

    def getMarchingCubes(self, density_x: int, density_y: int):
        def segment_func(v0, v1):
            self.segments.append(((v0[0] * self.scale_x, v0[1] * self.scale_y),
                                  (v1[0] * self.scale_x, v1[1] * self.scale_y)))

        def sample_func(point):
            x = int(point.x)
            y = self.t.height - 1 - int(point.y)
            # print(Level2.t.image.getpixel((x, y)))
            # if x < Level2.t.width and y < Level2.height
            return self.t.image.getpixel((x, y))[3] / 255

        pymunk.autogeometry.march_soft(pymunk.BB(0, 0, self.t.width-1, self.t.height-1), density_x, density_y,
                                       self.alpha_threshold, segment_func, sample_func)
        #ENLARGE texture
        #self.t.image = self.t.image.resize((int(self.t.width * self.scale_x), int(self.t.height * self.scale_y)))
        return self

    def sendSegmentsToPhysics(self, space):
        self.bd['new'] = pymunk.Body(1.0, 1.0, pymunk.Body.STATIC)
        space.add(self.bd['new'])
        #obj.bd[name].position = px, py
        for i in range(len(self.segments)):
            self.shp[str(i)] = pymunk.Segment(self.bd['new'], self.segments[i][0], self.segments[i][1], 1)
            space.add(self.shp[str(i)])
            self.shp[str(i)].friction = 0.99
            self.shp[str(i)].elasticity = 0.5

    def draw(self):
        arcade.draw_scaled_texture_rectangle(self.t.width, self.t.height, self.t, self.scale_x)
        # arcade.draw_texture_rectangle(self.t.width / 2, self.t.height / 2, self.t.width,
        #                               self.t.height, self.t)
        for i in self.segments:
            arcade.draw_line(i[0][0], i[0][1], i[1][0], i[1][1], arcade.color.LEMON, 1)

class PhysicsDumper():
    def __init__(self, filename, filepath, sep='\\'):
        self.path = filepath + sep + filename

    def dumpBody(self, bodiesElem: Optional[ET.Element], b: str, obj):
        body: Optional[pymunk.Body] = obj.bd[b]
        xmlbody: Optional[ET.SubElement] = ET.SubElement(bodiesElem, 'body')
        if body.body_type == pymunk.Body.DYNAMIC:
            xmlbody.set("type", "DYNAMIC")
        elif body.body_type == pymunk.Body.KINEMATIC:
            xmlbody.set("type", "KINEMATIC")
        elif body.body_type == pymunk.Body.STATIC:
            xmlbody.set("type", "STATIC")
        xmlbody.set("position_x", str(body.position.x))
        xmlbody.set("position_y", str(body.position.y))
        xmlbody.set("id", b)
        xmlbody.set("mass", str(body.mass))
        xmlbody.set("moment", str(body.moment))
        for s in body.shapes:
            for shp in obj.shp:
                if obj.shp[shp] == s:
                    self.dumpShape(xmlbody, shp, obj)
                    break

    def dumpShape(self, bodyElement, shp, obj):
        s = obj.shp[shp]
        xmlshape = ET.SubElement(bodyElement, 'shape')
        xmlshape.set("id", shp)
        xmlshape.set("elasticity", str(s.elasticity))
        xmlshape.set("friction", str(s.friction))
        xmlshape.set("density", str(s.density))
        xmlshape.set("radius", str(s.radius))
        if s.__class__.__name__ == "Segment":
            xmlshape.set("a_x", str(s.a[0]))
            xmlshape.set("a_y", str(s.a[1]))
            xmlshape.set("b_x", str(s.b[0]))
            xmlshape.set("b_y", str(s.b[1]))
            xmlshape.set("type", 'SEGMENT')
        elif s.__class__.__name__ == "Poly":
            v = s.get_vertices()
            s = " ".join(str(i.x) + " " + str(i.y) for i in v)
            xmlshape.text = s
            xmlshape.set("type", "POLY")
        elif s.__class__.__name__ == "Circle":
            xmlshape.set("offset_x", str(s.offset.x))
            xmlshape.set("offset_y", str(s.offset.y))
            xmlshape.set("type", 'CIRCLE')

    def dumpConstraints(self, constraintsElement, c, obj):
        cns: Optional[pymunk.Constraint] = obj.cns[c]
        constraint = ET.SubElement(constraintsElement, 'constraint')
        ba = None
        bb = None
        for body in obj.bd:
            if cns.a == obj.bd[body]:
                ba = body
            elif cns.b == obj.bd[body]:
                bb = body
            if ba and bb:
                break
        constraint.set("id", c)
        constraint.set("a", ba)
        constraint.set("b", bb)

        if cns.__class__.__name__ == "PinJoint":
            constraint.set("type", "PinJoint")
            constraint.set("anchor_a_x", str(cns.anchor_a[0]))
            constraint.set("anchor_a_y", str(cns.anchor_a[1]))
            constraint.set("anchor_b_x", str(cns.anchor_b[0]))
            constraint.set("anchor_b_y", str(cns.anchor_b[1]))
            constraint.set("distance", str(cns.distance))

        elif cns.__class__.__name__ == "SlideJoint":
            constraint.set("type", "SlideJoint")
            constraint.set("anchor_a_x", str(cns.anchor_a[0]))
            constraint.set("anchor_a_y", str(cns.anchor_a[1]))
            constraint.set("anchor_b_x", str(cns.anchor_b[0]))
            constraint.set("anchor_b_y", str(cns.anchor_b[1]))
            constraint.set("max", str(cns.max))
            constraint.set("min", str(cns.min))

        elif cns.__class__.__name__ == "PivotJoint":
            constraint.set("anchor_a_x", str(cns.anchor_a[0]))
            constraint.set("anchor_a_y", str(cns.anchor_a[1]))
            constraint.set("anchor_b_x", str(cns.anchor_b[0]))
            constraint.set("anchor_b_y", str(cns.anchor_b[1]))

        elif cns.__class__.__name__ == "GrooveJoint":
            constraint.set("type", "GrooveJoint")
            constraint.set("groove_a_x", str(cns.groove_a[0]))
            constraint.set("groove_a_y", str(cns.groove_a[1]))
            constraint.set("groove_b_x", str(cns.groove_b[0]))
            constraint.set("groove_b_y", str(cns.groove_b[1]))
            constraint.set("anchor_b_x", str(cns.anchor_b[0]))
            constraint.set("anchor_b_y", str(cns.anchor_b[1]))

        elif cns.__class__.__name__ == "DampedSpring":
            constraint.set("type", "DampedSpring")
            constraint.set("anchor_a_x", str(cns.anchor_a[0]))
            constraint.set("anchor_a_y", str(cns.anchor_a[1]))
            constraint.set("anchor_b_x", str(cns.anchor_b[0]))
            constraint.set("anchor_b_y", str(cns.anchor_b[1]))
            constraint.set("rest_length", str(cns.rest_length))
            constraint.set("stiffness", str(cns.stiffness))
            constraint.set("damping", str(cns.damping))

        elif cns.__class__.__name__ == "DampedRotarySpring":
            constraint.set("type", "DampedRotarySpring")
            constraint.set("rest_angle", str(cns.rest_angle))
            constraint.set("stiffness", str(cns.stiffness))
            constraint.set("damping", str(cns.damping))

        elif cns.__class__.__name__ == "RotaryLimitJoint":
            constraint.set("type", "RotaryLimitJoint")
            constraint.set("max", str(cns.max))
            constraint.set("min", str(cns.min))

        elif cns.__class__.__name__ == "RatchetJoint":
            constraint.set("type", "RatchetJoint")
            constraint.set("phase", str(cns.phase))
            constraint.set("ratchet", str(cns.ratchet))
            constraint.set("angle", str(cns.angle))

        elif cns.__class__.__name__ == "GearJoint":
            constraint.set("type", "GearJoint")
            constraint.set("phase", str(cns.phase))
            constraint.set("ratio", str(cns.ratio))

        elif cns.__class__.__name__ == "SimpleMotor":
            constraint.set("type", "SimpleMotor")
            constraint.set("rate", str(cns.rate))

        constraint.set("error_bias", str(cns.error_bias))
        constraint.set("max_bias", str(cns.max_bias))
        constraint.set("max_force", str(cns.max_force))

    def dumpData(self, obj):
        root = ET.Element('root')
        bodies = ET.SubElement(root, 'bodies')

        for b in obj.bd:
            self.dumpBody(bodies, b, obj)

        constraints = ET.SubElement(root, 'constraints')

        for c in obj.cns:
            self.dumpConstraints(constraints, c, obj)

        f = open(self.path, "w")
        f.write(str(ET.tostring(root, encoding="unicode")))
        f.close()

    def readShape(self, shape, body, obj, space):
        stype = shape.attrib['type']
        elasticity = float(shape.attrib["elasticity"]) if shape.attrib["elasticity"] != 'inf' else pymunk.inf
        friction = float(shape.attrib["friction"]) if shape.attrib["friction"] != 'inf' else pymunk.inf
        density = float(shape.attrib["density"]) if shape.attrib["density"] != 'inf' else pymunk.inf
        radius = float(shape.attrib["radius"])
        sname = shape.attrib["id"]

        if stype == "SEGMENT":
            a_x = float(shape.attrib["a_x"])  # + px
            a_y = float(shape.attrib["a_y"])  # + py
            b_x = float(shape.attrib["b_x"])  # + px
            b_y = float(shape.attrib["b_y"])  # + py
            obj.shp[sname] = pymunk.Segment(body, (a_x, a_y), (b_x, b_y), radius)
            space.add(obj.shp[sname])
            obj.shp[sname].friction = friction
            if density > 0.0:
                obj.shp[sname].density = density
            obj.shp[sname].elasticity = elasticity

        elif stype == "CIRCLE":
            o_x = float(shape.attrib["offset_x"])
            o_y = float(shape.attrib["offset_y"])
            obj.shp[sname] = pymunk.Circle(body, radius, (o_x, o_y))
            space.add(obj.shp[sname])
            obj.shp[sname].friction = friction
            if density > 0.0:
                obj.shp[sname].density = density

            obj.shp[sname].elasticity = elasticity

        elif stype == "POLY":
            verts = shape.text.split()
            tmp = [(float(verts[i]), float(verts[i + 1])) for i in range(0, len(verts), 2)]
            obj.shp[sname] = pymunk.Poly(body, tmp, None, radius)
            space.add(obj.shp[sname])
            obj.shp[sname].friction = friction
            if density > 0.0:
                obj.shp[sname].density = density
            obj.shp[sname].elasticity = elasticity

    def readBody(self, body, obj, space):
        type = body.attrib['type']
        if type == 'DYNAMIC':
            type = pymunk.Body.DYNAMIC
        elif type == "KINEMATIC":
            type = pymunk.Body.KINEMATIC
        else:
            type = pymunk.Body.STATIC
        px = float(body.attrib["position_x"])
        py = float(body.attrib["position_y"])
        name = body.attrib["id"]
        mass = float(body.attrib["mass"]) if body.attrib["mass"] != 'inf' else pymunk.inf
        moment = float(body.attrib["moment"]) if body.attrib["moment"] != 'inf' else pymunk.inf
        obj.bd[name] = pymunk.Body(mass, moment, type)
        space.add(obj.bd[name])
        obj.bd[name].position = px, py
        for shape in body:
            if shape.tag == 'shape':
                self.readShape(shape, obj.bd[name], obj, space)

    def readConstraint(self, c, obj, space):
        cntype = c.attrib['type']
        cname = c.attrib['id']
        a = obj.bd[c.attrib['a']]
        b = obj.bd[c.attrib['b']]
        # TODO [EH] add missing constraints
        if cntype == 'GrooveJoint':
            g_a_x = float(c.attrib['groove_a_x'])
            g_a_y = float(c.attrib['groove_a_y'])
            g_b_x = float(c.attrib['groove_b_x'])
            g_b_y = float(c.attrib['groove_b_y'])
            a_b_x = float(c.attrib['anchor_b_x'])
            a_b_y = float(c.attrib['anchor_b_y'])
            obj.cns[cname] = pymunk.GrooveJoint(a, b, (g_a_x, g_a_y), (g_b_x, g_b_y), (a_b_x, a_b_y))

        elif cntype == 'DampedSpring':
            a_a_x = float(c.attrib['anchor_a_x'])
            a_a_y = float(c.attrib['anchor_a_y'])
            a_b_x = float(c.attrib['anchor_b_x'])
            a_b_y = float(c.attrib['anchor_b_y'])
            rest_length = float(c.attrib['rest_length'])
            stiffness = float(c.attrib['stiffness'])
            damping = float(c.attrib['damping'])
            obj.cns[cname] = pymunk.DampedSpring(a, b, (a_a_x, a_a_y), (a_b_x, a_b_y), rest_length,
                                                 stiffness, damping)

        space.add(obj.cns[cname])
        error_bias = float(c.attrib["error_bias"]) if c.attrib["error_bias"] != 'inf' else pymunk.inf
        max_bias = float(c.attrib["max_bias"]) if c.attrib["max_bias"] != 'inf' else pymunk.inf
        max_force = float(c.attrib["max_force"]) if c.attrib["max_force"] != 'inf' else pymunk.inf
        obj.cns[cname].error_bias = error_bias
        obj.cns[cname].max_bias = max_bias
        obj.cns[cname].max_force = max_force

    def readData(self, obj, space):
        tree = ET.parse(self.path)
        root = tree.getroot()
        for child in root:
            if child.tag == 'bodies':
                for body in child:
                    self.readBody(body, obj, space)

        for child in root:
            if child.tag == 'constraints':
                for c in child:
                    self.readConstraint(c, obj, space)


class Level:

    # TODO [EH] add reset of level per key press

    def __init__(self):
        self.bd = {}
        self.shp = {}
        self.cns = {}
        self.type = "xml"

    def remove(self, space):
        for v in self.cns:
            space.remove(self.cns[v])
        for v in self.shp:
            space.remove(self.shp[v])
        for v in self.bd:
            space.remove(self.bd[v])

    def create(self, space):

        PhysicsDumper('_level.xml', EXEC_FOLDER).readData(self, space)
        #PhysicsDumper('_level.xml', EXEC_FOLDER).dumpData(self)

    def draw(self):
        for s in self.shp:
            shape = self.shp[s]
            if shape.__class__.__name__ == "Poly":
                bpos = shape.body.position
                poly = shape.get_vertices()
                for v in range(len(poly) - 1):
                    arcade.draw_line(poly[v][0] + bpos[0], poly[v][1] + bpos[1], poly[v + 1][0] + bpos[0],
                                     poly[v + 1][1] + bpos[1], arcade.color.BLACK, 1)
                arcade.draw_line(poly[-1][0] + bpos[0], poly[-1][1] + bpos[1], poly[0][0] + bpos[0],
                                 poly[0][0] + bpos[1],
                                 arcade.color.BLACK, 1)
            elif shape.__class__.__name__ == "Segment":
                bpos = shape.body.position
                arcade.draw_line(shape.a[0] + bpos[0], shape.a[1] + bpos[1], shape.b[0] + bpos[0], shape.b[1] + bpos[1],
                                 arcade.color.BLACK, 1)


class Bike:

    # TODO [EH] change this class into Vehicle

    def __init__(self):
        self.bd = {}
        self.shp = {}
        self.cns = {}
        self.dir = 1  # TODO [EH] create some normal directions maybe, now 1 is left wheel, -1 is right wheel

    def remove(self, space):
        for v in self.cns:
            space.remove(self.cns[v])
        for v in self.shp:
            space.remove(self.shp[v])
        for v in self.bd:
            space.remove(self.bd[v])

    def create(self, space):
        PhysicsDumper('_bike.xml', EXEC_FOLDER).readData(self, space)
        #PhysicsDumper('_bike.xml', EXEC_FOLDER).dumpData(self)

    def draw(self):
        for s in self.shp:
            shape = self.shp[s]
            bpos = shape.body.position
            arcade.draw_circle_filled(shape.offset[0] + bpos[0], shape.offset[1] + bpos[1], shape.radius,
                                      arcade.color.CYAN)


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        # Physics engine wrapper TODO [EH] change to direct pymunk
        self.physics_engine = Optional[arcade.PymunkPhysicsEngine]

        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

        # display mechanism in arcade
        self.player_list: Optional[arcade.SpriteList] = None

        self.bike = None
        self.level = None

        #self.level2 = None
        self.ang_vel = 0
        self.music = None
        self.prevtime = time.time()
        self.munktime = time.time()
        self.update_time = 0
        self.set_update_rate(1/60)

        self.processPhysics = True
        self.drawGraphics = True
        self.drawText = True
        self.printPhysicElems = False

        self.help = ''''w' and 's' to steer, ' ' to change wheels,
'z' to dump level and bike to xml, 'x' to hide text,
'c' to hide graphics, 'v' to ignore physics
'b' to reload bike, 'n' to reload level'''

        print(self.help)
        self.fn = EXEC_FOLDER + '\\Pacifico.ttf'
        self.cwd = "Current Working Dir = " + EXEC_FOLDER

    def setup(self):
        """ Set up the game here. Call this function to restart the game. """

        # TODO [EH] how does this work? Should 1 game have one Window? if yes, when to call this func (how load
        # new levels? Should main loop be stopped? :|

        # TODO [EH] remove this (then direct call to pymunk step/update will need to be added to main loop)
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=1,
                                                         gravity=(0, -100))

        self.bike = Bike()
        #self.level = Level()
        #self.level2 = Level2()
        self.level = Level2()

        #PhysicsDumper('_level2.xml', EXEC_FOLDER).dumpData(self.level2)
        self.bike.create(self.physics_engine.space)
        self.level.create(self.physics_engine.space)
        self.music = arcade.Sound(":resources:music/1918.mp3", streaming=True)
        self.music.play(0.02)

    # def draw_lines(self, arr):
    #     for i in arr:
    #         arcade.draw_line(i[0][0], i[0][1], i[1][0], i[1][1], arcade.color.LEMON, 1)
    #
    # def draw_shapes(self, shape, thickness, color):
    #     if shape.__class__.__name__ == "Poly":
    #         bpos = shape.body.position
    #         poly = shape.get_vertices()
    #         for v in range(len(poly) - 1):
    #             arcade.draw_line(poly[v][0]+bpos[0], poly[v][1]+bpos[1], poly[v+1][0]+bpos[0], poly[v+1][1]+bpos[1], color, thickness)
    #         arcade.draw_line(poly[-1][0]+bpos[0], poly[-1][1]+bpos[1], poly[0][0]+bpos[0], poly[0][0]+bpos[1], color, thickness)
    #     elif shape.__class__.__name__ == "Segment":
    #         bpos = shape.body.position
    #         arcade.draw_line(shape.a[0]+bpos[0], shape.a[1]+bpos[1], shape.b[0]+bpos[0], shape.b[1]+bpos[1], color, thickness)
    #     elif shape.__class__.__name__ == "Circle":
    #         bpos = shape.body.position
    #         arcade.draw_circle_filled(shape.offset[0]+bpos[0], shape.offset[1]+bpos[1], shape.radius, color)

    def print_physic_elems(self, body_dict, body_id):
        b = body_dict[body_id]
        print(body_id)
        print("angle ", b.angle, "angular_velocity", b.angular_velocity)
        print("force ", b.force, "kinetic_energy", b.kinetic_energy)
        print("mass ", b.mass, "moment", b.moment)
        print("position ", b.position, "rotation_vector", b.rotation_vector)
        print("torque", b.torque, "velocity", b.velocity)
        for s in b.shapes:
            print("child shape surface vel", s.surface_velocity)

    def on_draw(self):
        """ Render the screen. """
        t = time.time()

        # is it needed to be called every time on start of this func?
        # it is -> clearing buffers before drawing
        # TODO [EH] - needs to be checked if a direct call to get_window().clear() could be done in place of bazillion
        # calls to subclasses etc... (not object oriented though)
        arcade.start_render()

        v = arcade.get_viewport()
        if self.drawGraphics:

            self.level.draw()
            self.bike.draw()
            #self.level2.draw()

            #arcade.draw_texture_rectangle(self.level2.t.width/2, self.level2.t.height/2, self.level2.t.width, self.level2.t.height, self.level2.t)

            # for shp in self.level.shp:
            #     self.draw_shapes(self.level.shp[shp], 1, arcade.color.BLACK)
            #
            # for shp in self.bike.shp:
            #     self.draw_shapes(self.bike.shp[shp], 1, arcade.color.CYAN)

            #self.draw_lines(self.level2.segments)

        if self.drawText:
            pass
            # arcade.draw_text("UPDATE  " + str(1000 * self.update_time) + "ms", v[0] + 700, v[2] + 90,
            #                  arcade.color.BLACK, 12, font_name=self.fn)
            # arcade.draw_text(self.cwd, v[0] + 700, v[2] + 75, arcade.color.BLACK, 12, font_name=self.fn)
            # arcade.draw_text("DRAWING " + str(1000 * (time.time() - t)) + "ms", v[0] + 700, v[2] + 60,
            #                  arcade.color.BLACK, 12, font_name=self.fn)
            # arcade.draw_text("PHYSICS " + str(1000 * self.munktime) + "ms", v[0] + 700, v[2] + 45, arcade.color.BLACK,
            #                  12, font_name=self.fn)
            # arcade.draw_text("WHOLE F " + str(1000 * (time.time() - self.prevtime)) + "ms", v[0] + 700, v[2] + 30,
            #                  arcade.color.BLACK, 12, font_name=self.fn)
            # arcade.draw_text(self.help, v[0] + 20, v[2] + 90, arcade.color.BLACK, 12, font_name=self.fn)
            #
            # dt = time.time() - self.prevtime
            # dt = 0.001 if dt <= 0.001 else dt
            #
            # arcade.draw_text("FPS---- " + str(1 / (dt)) + "fps", v[0] + 700, v[2] + 15, arcade.color.BLACK, 12,
            #                  font_name=self.fn)

        else:
            dt = time.time() - self.prevtime
            dt = 0.001 if dt <= 0.001 else dt
            print("FPS---- " + str(1 / (dt)) + "fps")

        if self.printPhysicElems:
            self.print_physic_elems(self.bike.bd, 'rw')

        self.prevtime = t

        # self.player_list.draw()

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """
        if key == arcade.key.W:
            self.ang_vel = -20 * self.bike.dir
        elif key == arcade.key.S:
            self.ang_vel = 20 * self.bike.dir
        elif key == arcade.key.SPACE:
            self.bike.dir *= -1
        elif key == arcade.key.Z:
            PhysicsDumper('bike.xml', EXEC_FOLDER).dumpData(self.bike)
            PhysicsDumper('level.xml', EXEC_FOLDER).dumpData(self.level)
        elif key == arcade.key.X:
            self.drawText = not self.drawText
        elif key == arcade.key.C:
            self.drawGraphics = not self.drawGraphics
        elif key == arcade.key.V:
            self.processPhysics = not self.processPhysics
        elif key == arcade.key.B:
            self.bike.remove(self.physics_engine.space)
            self.bike.create(self.physics_engine.space)
        elif key == arcade.key.N:
            type = self.level.type[:]
            self.level.remove(self.physics_engine.space)
            del self.level
            self.level = None
            if type == 'xml':
                self.level = Level2()
            else:
                self.level = Level()
            self.level.create(self.physics_engine.space)
        elif key == arcade.key.M:
            self.printPhysicElems = not self.printPhysicElems
        elif key == arcade.key.ESCAPE:
            self.close()
        elif key == arcade.key.D:
            self.bike.bd['rw'].apply_force_at_local_point((11120, -11120.0), (0, -10))
        elif key == arcade.key.A:
            self.bike.bd['rw'].apply_force_at_local_point((-11120, -11120.0), (0, -10))

    def on_close(self):
        print("Closing this")
        self.close()

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """
        self.ang_vel = 0

    def on_update(self, delta_time):
        """ Movement and game logic """
        t = time.time()
        self.update_time = delta_time
        if self.bike.dir > 0:
            obj = self.bike.bd['lw']
        else:
            obj = self.bike.bd['rw']

        # set angular velocity for every frame
        obj.angular_velocity = self.ang_vel

        # TODO [EH] this will be threw out (??)
        # TODO [EH] if during setup direct boot of pymunk will be set in place of self.physics_engine, then yep!
        # self.physics_engine.space.step(1/60)
        if self.processPhysics:
            self.physics_engine.step()

        # Do the scrolling
        arcade.set_viewport(self.bike.bd['head'].position.x - SCREEN_WIDTH/2,
                            self.bike.bd['head'].position.x + SCREEN_WIDTH/2,
                            self.bike.bd['head'].position.y - SCREEN_HEIGHT/2,
                            self.bike.bd['head'].position.y + SCREEN_HEIGHT/2)

        self.munktime = time.time() - t


def main():
    """ Main method """
    # TODO [EH] -> check in sources what is this and could it be changed into direct calls?
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    if not sys.executable.endswith("python.exe"):
        EXEC_FOLDER = sys.executable[:sys.executable.rfind('\\')]
    if len(sys.argv) > 1:
        pass
    else:
        main()

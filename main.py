"""
The GAME
"""
import os
import sys
import math
import time
import arcade
import pymunk

from typing import Optional  # TODO [EH] wut is this??????
import xml.etree.ElementTree as ET

# TODO [EH] shall it stay global? Move it into direct call?
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Platformer"

EXEC_FOLDER = os.getcwd()


class PhysicsDumper():
    def __init__(self, filename, filepath, sep='\\'):
        self.path = filepath + sep + filename

    def dumpData(self, obj):
        root = ET.Element('root')
        bodies = ET.SubElement(root, 'bodies')

        for b in obj.bd:
            body = obj.bd[b]
            xmlbody = ET.SubElement(bodies, 'body')
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
                        xmlshape = ET.SubElement(xmlbody, 'shape')
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
                        break

        constraints = ET.SubElement(root, 'constraints')
        for c in obj.cns:
            cns = obj.cns[c]
            constraint = ET.SubElement(constraints, 'constraint')
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
            if cns.__class__.__name__ == "GrooveJoint":
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

        f = open(self.path, "w")
        f.write(str(ET.tostring(root, encoding="unicode")))
        #print(str(ET.tostring(root, encoding="unicode")))
        #print(self.path)
        f.close()

    def readData(self, obj, space):
        tree = ET.parse(self.path)
        root = tree.getroot()
        for child in root:
            if child.tag == 'bodies':
                for body in child:
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
                            stype = shape.attrib['type']
                            elasticity = float(shape.attrib["elasticity"]) if shape.attrib["elasticity"] != 'inf' else pymunk.inf
                            friction = float(shape.attrib["friction"]) if shape.attrib["friction"] != 'inf' else pymunk.inf
                            density = float(shape.attrib["density"]) if shape.attrib["density"] != 'inf' else pymunk.inf
                            radius = float(shape.attrib["radius"])
                            sname = shape.attrib["id"]

                            if stype == "SEGMENT":
                                a_x = float(shape.attrib["a_x"])# + px
                                a_y = float(shape.attrib["a_y"])# + py
                                b_x = float(shape.attrib["b_x"])# + px
                                b_y = float(shape.attrib["b_y"])# + py
                                obj.shp[sname] = pymunk.Segment(obj.bd[name], (a_x, a_y), (b_x, b_y), radius)
                                space.add(obj.shp[sname])
                                obj.shp[sname].friction = friction
                                if density > 0.0:
                                    obj.shp[sname].density = density
                                obj.shp[sname].elasticity = elasticity

                            elif stype == "CIRCLE":
                                o_x = float(shape.attrib["offset_x"])
                                o_y = float(shape.attrib["offset_y"])
                                obj.shp[sname] = pymunk.Circle(obj.bd[name], radius, (o_x, o_y))
                                space.add(obj.shp[sname])
                                obj.shp[sname].friction = friction
                                if density > 0.0:
                                    obj.shp[sname].density = density

                                obj.shp[sname].elasticity = elasticity

                            elif stype == "POLY":
                                verts = shape.text.split()
                                tmp = [(float(verts[i]), float(verts[i+1])) for i in range(0, len(verts), 2)]
                                obj.shp[sname] = pymunk.Poly(obj.bd[name], tmp, None, radius)
                                space.add(obj.shp[sname])
                                obj.shp[sname].friction = friction
                                if density > 0.0:
                                    obj.shp[sname].density = density
                                obj.shp[sname].elasticity = elasticity
        for child in root:
            if child.tag == 'constraints':
                for c in child:
                    cntype = c.attrib['type']
                    cname = c.attrib['id']
                    a = obj.bd[c.attrib['a']]
                    b = obj.bd[c.attrib['b']]
                    if cntype == 'GrooveJoint':
                        g_a_x = float(c.attrib['groove_a_x'])
                        g_a_y = float(c.attrib['groove_a_y'])
                        g_b_x = float(c.attrib['groove_b_x'])
                        g_b_y = float(c.attrib['groove_b_y'])
                        a_b_x = float(c.attrib['anchor_b_x'])
                        a_b_y = float(c.attrib['anchor_b_y'])

                        obj.cns[cname] = pymunk.GrooveJoint(a, b, (g_a_x, g_a_y), (g_b_x, g_b_y), (a_b_x, a_b_y))
                        space.add(obj.cns[cname])

                    elif cntype == 'DampedSpring':
                        a_a_x = float(c.attrib['anchor_a_x'])
                        a_a_y = float(c.attrib['anchor_a_y'])
                        a_b_x = float(c.attrib['anchor_b_x'])
                        a_b_y = float(c.attrib['anchor_b_y'])
                        rest_length = float(c.attrib['rest_length'])
                        stiffness = float(c.attrib['stiffness'])
                        damping = float(c.attrib['damping'])

                        obj.cns[cname] = pymunk.DampedSpring(a, b, (a_a_x, a_a_y), (a_b_x, a_b_y), rest_length, stiffness, damping)
                        space.add(obj.cns[cname])


class Level:

    # TODO [EH] add reset of level per key press

    def __init__(self):
        self.bd = {}
        self.shp = {}
        self.cns = {}

    def remove(self, space):
        for v in self.cns:
            space.remove(self.cns[v])
        for v in self.shp:
            space.remove(self.shp[v])
        for v in self.bd:
            space.remove(self.bd[v])

    def create(self, space):

        # self.bd['base'] = pymunk.Body(body_type=pymunk.Body.STATIC)
        # space.add(self.bd['base'])
        # self.bd['base'].position = (radius, radius)
        #
        # for i in range(elems):
        #     self.shp[str(i)] = pymunk.Segment(self.bd['base'], (self.line[i][0],   self.line[i][1]),
        #                               (self.line[i+1][0], self.line[i+1][1]), 1)
        #     self.shp[str(i)].friction = 10
        #     space.add(self.shp[str(i)])
        #
        # self.shp['yyy'] = pymunk.Poly(self.bd['base'], ((100, 100), (200, 200), (100, 200)))
        # self.shp['yyy'].friction = 10
        # space.add(self.shp['yyy'])
        # PhysicsDumper('_level.xml', EXEC_FOLDER).dumpData(self)

        PhysicsDumper('_level.xml', EXEC_FOLDER).readData(self, space)

        # self.line = []
        # for i in range(elems):
        #     self.line.append([math.sin(i * dr) * radius, math.cos(i*dr) * radius])
        # self.line.append([0, radius])
        # self.pos = [radius, radius]

class Bike:

    # TODO [EH] change this class into Vehicle
    # TODO [EH] add reset of bike per key press

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

        # general physics processing
        # TODO [EH] how could it be moved into xml?
        # overall processing is this:
        # 1 create body
        # 2 add body to space
        # 3 process body
        # 4 create shape
        # 5 add shape to space
        # 6 process shape
        # 7 create constraints
        # 8 add constraints to space
        # TODO [EH] how to clean it up before swapping levels???!
        # TODO [EH] store references in the table and then clean it? remove whole space? :|

        # # create body
        # self.bd['lw'] = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 15), body_type=pymunk.Body.DYNAMIC)
        # # add body to space
        # space.add(self.bd['lw'])
        # # modify body
        # self.bd['lw'].position = x - 30, y - 30
        # # create shape and add it to body
        # self.shp['lw1'] = pymunk.Circle(self.bd['lw'], 15)
        # # add shape to space
        # space.add(self.shp['lw1'])
        # # modify shape
        # self.shp['lw1'].elasticity = 0
        # self.shp['lw1'].friction = 0.7
        #
        # # repeat...
        # self.bd['rw'] = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 15), body_type=pymunk.Body.DYNAMIC)
        # space.add(self.bd['rw'])
        # self.bd['rw'].position = x + 30, y - 30
        # self.shp['rw1'] = pymunk.Circle(self.bd['rw'], 15)
        # space.add(self.shp['rw1'])
        # self.shp['rw1'].elasticity = 0
        # self.shp['rw1'].friction = 0.7
        #
        # self.bd['head'] = pymunk.Body(5, pymunk.moment_for_box(10, (80, 30)), body_type=pymunk.Body.DYNAMIC)
        # space.add(self.bd['head'])
        # self.bd['head'].position = x, y + 30
        # self.shp['head'] = pymunk.Circle(self.bd['head'], 15)
        # space.add(self.shp['head'])
        # self.shp['head'].elasticity = 0
        # self.shp['head'].friction = 0.7
        #
        # # 1. add constraints to bodies
        # # 2. add constraints to space
        # self.cns['lwGJ'] = pymunk.GrooveJoint(
        #     self.bd['head'], self.bd['lw'], (-30, -10), (-30, -40), (0, 0))
        # space.add(self.cns['lwGJ'])
        # # repeat...
        # self.cns['rwGJ'] = pymunk.GrooveJoint(
        #     self.bd['head'], self.bd['rw'], (30, -10), (30, -40), (0, 0))
        # space.add(self.cns['rwGJ'])
        # self.cns['lwDS'] = pymunk.DampedSpring(
        #     self.bd['head'], self.bd['lw'], (-30, 0), (0, 0), 50, 20, 10)
        # space.add(self.cns['lwDS'])
        # self.cns['rwDS'] = pymunk.DampedSpring(
        #     self.bd['head'], self.bd['rw'], (30, 0), (0, 0), 50, 20, 10)
        # space.add(self.cns['rwDS'])

        #PhysicsDumper('_bike.xml', EXEC_FOLDER).dumpData(self)

        PhysicsDumper('_bike.xml', EXEC_FOLDER).readData(self, space)


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        # Physics engine wrapper
        self.physics_engine = Optional[arcade.PymunkPhysicsEngine]

        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

        # display mechanism in arcade
        self.player_list: Optional[arcade.SpriteList] = None

        self.bike = None
        self.level = None
        self.ang_vel = 0
        self.music = None
        self.prevtime = time.time()
        self.munktime = time.time()
        self.update_time = 0
        self.set_update_rate(1/60)

        self.processPhysics = True
        self.drawGraphics = True
        self.drawText = True

        self.help = ''''w' and 's' to steer, ' ' to change wheels,
'z' to dump level and bike to xml, 'x' to hide text,
'c' to hide graphics, 'v' to ignore physics
'b' to reload bike, 'n' to reload level'''

    def setup(self):
        """ Set up the game here. Call this function to restart the game. """

        # TODO [EH] how does this work? Should 1 game have one Window? if yes, when to call this func (how load
        # new levels? Should main loop be stopped? :|

        # TODO [EH] remove this (then direct call to pymunk step/update will need to be added to main loop)
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=1,
                                                         gravity=(0, -100))

        self.bike = Bike()
        self.level = Level()
        self.bike.create(self.physics_engine.space)
        self.level.create(self.physics_engine.space)
        self.music = arcade.Sound(":resources:music/1918.mp3", streaming=True)
        self.music.play(0.02)

    def draw_shapes(self, shape, thickness, color):
        if shape.__class__.__name__ == "Poly":
            bpos = shape.body.position
            poly = shape.get_vertices()
            for v in range(len(poly) - 1):
                arcade.draw_line(poly[v][0]+bpos[0], poly[v][1]+bpos[1], poly[v+1][0]+bpos[0], poly[v+1][1]+bpos[1], color, thickness)
            arcade.draw_line(poly[-1][0]+bpos[0], poly[-1][1]+bpos[1], poly[0][0]+bpos[0], poly[0][0]+bpos[1], color, thickness)
        elif shape.__class__.__name__ == "Segment":
            bpos = shape.body.position
            arcade.draw_line(shape.a[0]+bpos[0], shape.a[1]+bpos[1], shape.b[0]+bpos[0], shape.b[1]+bpos[1], color, thickness)
        elif shape.__class__.__name__ == "Circle":
            bpos = shape.body.position
            arcade.draw_circle_filled(shape.offset[0]+bpos[0], shape.offset[1]+bpos[1], shape.radius, color)

    def on_draw(self):
        """ Render the screen. """

        # TODO [EH] add camera movement
        # is it needed to be called every time on start of this func?
        # it is -> clearing buffers before drawing
        # TODO [EH] - needs to be checked if a direct call to get_window().clear() could be done in place of bazillion
        # calls to subclasses etc... (not object oriented though)
        t = time.time()
        arcade.start_render()

        v = arcade.get_viewport()
        if self.drawGraphics:

            for shp in self.level.shp:
                self.draw_shapes(self.level.shp[shp], 1, arcade.color.BLACK)

            for shp in self.bike.shp:
                self.draw_shapes(self.bike.shp[shp], 1, arcade.color.CYAN)

        if self.drawText:
            arcade.draw_text("UPDATE  " + str(1000 * self.update_time) + "ms", v[0] + 700, v[2] + 90, arcade.color.BLACK, 12)
            arcade.draw_text(os.getcwd(), v[0] + 700, v[2] + 75, arcade.color.BLACK,12)
            arcade.draw_text("DRAWING " + str(1000 * (time.time() - t)) + "ms", v[0] + 700, v[2] + 60, arcade.color.BLACK, 12)
            arcade.draw_text("PHYSICS " + str(1000 * self.munktime) + "ms", v[0] + 700, v[2] + 45, arcade.color.BLACK, 12)
            arcade.draw_text("WHOLE F " + str(1000 * (time.time() - self.prevtime)) + "ms", v[0] + 700, v[2] + 30, arcade.color.BLACK, 12)
            arcade.draw_text(self.help, v[0] + 20, v[2] + 90, arcade.color.BLACK, 12)

        # p = self.level.pos
        # for i in range(len(self.level.line) - 1):
        #     arcade.draw_line(self.level.line[i][0]+p[0],
        #                      self.level.line[i][1]+p[1],
        #                      self.level.line[i+1][0]+p[0],
        #                      self.level.line[i+1][1]+p[1], arcade.color.BLACK, 1)
        #
        # # black wheel moves the bike
        # if self.bike.dir > 0:
        #     pos = self.bike.bd['lw'].position
        #     arcade.draw_circle_filled(pos[0], pos[1], 15, arcade.color.BLACK)
        #     pos = self.bike.bd['rw'].position
        #     arcade.draw_circle_filled(pos[0], pos[1], 15, arcade.color.AFRICAN_VIOLET)
        # else:
        #     pos = self.bike.bd['rw'].position
        #     arcade.draw_circle_filled(pos[0], pos[1], 15, arcade.color.BLACK)
        #     pos = self.bike.bd['lw'].position
        #     arcade.draw_circle_filled(pos[0], pos[1], 15, arcade.color.AFRICAN_VIOLET)
        #
        # pos = self.bike.bd['head'].position
        # arcade.draw_circle_filled(pos[0], pos[1], 15, arcade.color.ALLOY_ORANGE)

        dt = time.time() - self.prevtime
        dt = 0.001 if dt <= 0.001 else dt
        self.prevtime = t
        arcade.draw_text("FPS---- " + str(1/(dt)) + "fps", v[0] + 700, v[2] + 15, arcade.color.BLACK, 12)

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
            self.level.remove(self.physics_engine.space)
            self.level.create(self.physics_engine.space)

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

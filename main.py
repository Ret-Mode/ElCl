"""
The GAME
"""
import os
import sys
import math
import time

# game imports
import arcade
import pymunk

# profiling
import cProfile
import pstats

# file handling
import xml.etree.ElementTree as ET

# PyCharm type helper
from typing import Optional

# TODO [EH] shall it stay global? Move it into direct call?
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Platformer"

EXEC_FOLDER = os.getcwd()


# temporary - don't know where to put those functions really :D
class Util:

    @staticmethod
    def drawVectors(shapeDict):
        for s in shapeDict:
            shape = shapeDict[s]
            if shape.__class__.__name__ == "Poly":
                bpos = shape.body.position
                poly = shape.get_vertices()
                for v in range(len(poly) - 1):
                    x, y = poly[v].rotated(shape.body.angle) + bpos
                    x2, y2 = poly[v+1].rotated(shape.body.angle) + bpos
                    arcade.draw_line(x, y, x2, y2, arcade.color.BLACK, 1)
                x, y = poly[-1].rotated(shape.body.angle) + bpos
                x2, y2 = poly[0].rotated(shape.body.angle) + bpos
                arcade.draw_line(x, y, x2, y2, arcade.color.BLACK, 1)
            elif shape.__class__.__name__ == "Segment":
                bpos = shape.body.position
                arcade.draw_line(shape.a[0] + bpos[0], shape.a[1] + bpos[1], shape.b[0] + bpos[0], shape.b[1] + bpos[1],
                                 arcade.color.YELLOW, 1)
            elif shape.__class__.__name__ == "Circle":
                bpos = shape.body.position
                arcade.draw_circle_filled(bpos[0], bpos[1], shape.radius,
                                 arcade.color.GREEN, 1)

    @staticmethod
    def getAllEntityFiles(path):
        output = []
        filesList = os.listdir(path)
        for f in filesList:
            if f.endswith(".xml"):
                output.append(path + f)
        # currently selected car
        output.append(0)
        return output

    @staticmethod
    def getNextEntity(entityList):
        entityList[-1] = (entityList[-1] + 1) % (len(entityList) - 1)

        return entityList[entityList[-1]]

    @staticmethod
    def getVehiclePath():
        return EXEC_FOLDER + '\\vehicles\\'

    @staticmethod
    def getLevelsPath():
        return EXEC_FOLDER + '\\levels\\'

    @staticmethod
    def getFolderFromFilePath(filePath):
        return filePath[:filePath.rfind('\\')]

    @staticmethod
    def getFileFromOtherFilePath(filePath, file):
        return Util.getFolderFromFilePath(filePath) + '\\' + file



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


# TODO [EH] move this to separate file
# TODO [EH] add defaults to unnecessary fields
class PhysicsDumper():
    def __init__(self):
        pass

    # TODO [EH] - chop this even more?
    def dumpData(self, path, obj):
        root = ET.Element('root')
        root.set("type", obj.type)

        if obj.type == 'vehicle':
            root.set("speed", str(obj.speed))
            bodies = ET.SubElement(root, 'bodies')
            for b in obj.bd:
                self.dumpBodyWithTex(bodies, b, obj)
        elif obj.type == 'autogeometry':
            self.dumpAutogeometry(root, obj)
        elif obj.type == 'level':
            root.set("player_x", str(obj.player_x))
            root.set("player_y", str(obj.player_y))
            bodies = ET.SubElement(root, 'bodies')
            for b in obj.bd:
                self.dumpBody(bodies, b, obj)
        else:
            bodies = ET.SubElement(root, 'bodies')
            for b in obj.bd:
                self.dumpBody(bodies, b, obj)

        constraints = ET.SubElement(root, 'constraints')

        for c in obj.cns:
            self.dumpConstraints(constraints, c, obj)

        # NOTE [EH] fix newlines
        xml_s = ET.tostring(root, encoding="unicode").replace('</root>', '\n</root>')
        for i in ['<bodies>', '</bodies>', '<bodies />', '<constraints>', '<constraints />', '</constraints>']:
            xml_s = xml_s.replace(i, '\n '+ i)
        for i in ['<body ', '</body>', '<body />', '<constraint ', '</constraint>', '<constraint /> ']:
            xml_s = xml_s.replace(i, '\n  ' + i)
        for i in ['<shape ', '</shape>', '<shape />']:
            xml_s = xml_s.replace(i, '\n   ' + i)

        f = open(path, "w")
        f.write(str(xml_s))
        f.close()

    def dumpAutogeometry(self, rootElem: Optional[ET.Element], obj):
        texName: Optional[str] = obj.t.name
        baseDir = EXEC_FOLDER
        if obj.type == 'vehicle':
            baseDir = Util.getVehiclePath()
        elif obj.type == 'autogeometry' or obj.type == 'level':
            baseDir = Util.getLevelsPath()
        if texName.startswith(baseDir):
            texName = texName[len(baseDir):texName.find('.png') + 4]
            if texName[0] == '\\' or texName[0] == '/':
                texName = texName[1:]
        rootElem.set("texture", texName)
        rootElem.set("density_x", str(obj.density_x))
        rootElem.set("density_y", str(obj.density_y))
        rootElem.set("scale", str(obj.scale))
        rootElem.set("alpha_threshold", str(obj.alpha_threshold))
        rootElem.set("friction", str(obj.friction))
        rootElem.set("elasticity", str(obj.elasticity))

        rootElem.set("player_x", str(obj.player_x))
        rootElem.set("player_y", str(obj.player_y))

    def dumpBodyWithTex(self, bodiesElem: Optional[ET.Element], b: str, obj):
        body: Optional[pymunk.Body] = obj.bd[b]
        texName: Optional[str] = obj.bdTex[b].texture.name
        baseDir = EXEC_FOLDER
        if obj.type == 'vehicle':
            baseDir = Util.getVehiclePath()
        elif obj.type == 'autogeometry' or obj.type == 'level':
            baseDir = Util.getLevelsPath()
        if texName.startswith(baseDir):
            texName = texName[len(baseDir):texName.find('.png')+4]
            if texName[0] == '\\' or texName[0] == '/':
                texName = texName[1:]
        xmlbody: Optional[ET.SubElement] = ET.SubElement(bodiesElem, 'body')
        xmlbody.set("texture", texName)
        xmlbody.set("texture_rotation", "True" if obj.bdTex[b].texture_rotation else 'False')
        xmlbody.set("texture_scale", str(obj.bdTex[b].scale))
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

        # TODO [EH] not obligatory
        xmlshape.set("density", str(s.density))

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

        # TODO [EH] not obligatory data
        constraint.set("collide_bodies", str(cns.collide_bodies))
        constraint.set("error_bias", str(cns.error_bias))
        constraint.set("max_bias", str(cns.max_bias))
        constraint.set("max_force", str(cns.max_force))

    def readData(self, path, space):
        tree = ET.parse(path)
        root = tree.getroot()
        obj = None
        if 'type' in root.attrib:

            if root.attrib["type"] == 'autogeometry':
                # damn, swapped obj and path args :(
                obj = Level2()
                obj.type = root.attrib["type"]
                self.readAutogeometry(root, obj, path)
                obj.getMarchingCubes(obj.density_x, obj.density_y).sendSegmentsToPhysics(space)
                return obj

            elif root.attrib["type"] == 'level':
                obj = Level()
                obj.type = root.attrib["type"]
                obj.player_x = float(root.attrib["player_x"])
                obj.player_y = float(root.attrib["player_y"])

            elif root.attrib["type"] == 'vehicle':
                obj = Vehicle()
                obj.type = root.attrib["type"]
                obj.speed = float(root.attrib['speed'])

            else:
                obj = Level()
                obj.type = 'level'

        for child in root:
            if child.tag == 'bodies':
                for body in child:
                    if 'texture' in body.attrib:
                        # damn, swapped obj and path args :(
                        self.readBodyWithTex(body, obj, space, path)
                    else:
                        self.readBody(body, obj, space)

        for child in root:
            if child.tag == 'constraints':
                for c in child:
                    self.readConstraint(c, obj, space)

        return obj

    def readAutogeometry(self, root: Optional[ET.Element], obj, path: str):
        obj.t = arcade.load_texture(Util.getFileFromOtherFilePath(path, root.attrib["texture"]))
        obj.density_x = int(root.attrib["density_x"])
        obj.density_y = int(root.attrib["density_y"])
        obj.scale = float(root.attrib["scale"])
        obj.alpha_threshold = float(root.attrib["alpha_threshold"])
        obj.friction = float(root.attrib["friction"])
        obj.elasticity = float(root.attrib["elasticity"])

        obj.player_x = float(root.attrib["player_x"])
        obj.player_y = float(root.attrib["player_y"])

    def readBodyWithTex(self, body, obj, space, path: str):
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

        obj.bdTex[name]: arcade.Sprite = arcade.Sprite(Util.getFileFromOtherFilePath(path, body.attrib["texture"]))
        obj.bdTex[name].texture_rotation = True if body.attrib["texture_rotation"] == 'True' else False
        obj.bdTex[name].scale = float(body.attrib['texture_scale'])
        #obj.bdTex[name].texture_transform.scale(obj.bdTex[name].texture_scale_x, obj.bdTex[name].texture_scale_y)

        for shape in body:
            if shape.tag == 'shape':
                self.readShape(shape, obj.bd[name], obj, space)

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

    def readConstraint(self, c, obj, space):
        cntype = c.attrib['type']
        cname = c.attrib['id']
        a = obj.bd[c.attrib['a']]
        b = obj.bd[c.attrib['b']]

        if cntype == 'PinJoint':
            a_a_x = float(c.attrib['anchor_a_x'])
            a_a_y = float(c.attrib['anchor_a_y'])
            a_b_x = float(c.attrib['anchor_b_x'])
            a_b_y = float(c.attrib['anchor_b_y'])
            distance = float(c.attrib['distance'])
            obj.cns[cname] = pymunk.PinJoint(a, b, (a_a_x, a_a_y), (a_b_x, a_b_y))
            obj.cns[cname].distance = distance

        elif cntype == 'SlideJoint':
            a_a_x = float(c.attrib['anchor_a_x'])
            a_a_y = float(c.attrib['anchor_a_y'])
            a_b_x = float(c.attrib['anchor_b_x'])
            a_b_y = float(c.attrib['anchor_b_y'])
            min = float(c.attrib['min'])
            max = float(c.attrib['max'])
            obj.cns[cname] = pymunk.SlideJoint(a, b, (a_a_x, a_a_y), (a_b_x, a_b_y), min, max)

        elif cntype == 'PivotJoint':
            a_a_x = float(c.attrib['anchor_a_x'])
            a_a_y = float(c.attrib['anchor_a_y'])
            a_b_x = float(c.attrib['anchor_b_x'])
            a_b_y = float(c.attrib['anchor_b_y'])
            obj.cns[cname] = pymunk.PivotJoint(a, b, (a_a_x, a_a_y), (a_b_x, a_b_y))

        elif cntype == 'GrooveJoint':
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

        elif cntype == 'DampedRotarySpring':
            a_a_x = float(c.attrib['anchor_a_x'])
            a_a_y = float(c.attrib['anchor_a_y'])
            a_b_x = float(c.attrib['anchor_b_x'])
            a_b_y = float(c.attrib['anchor_b_y'])
            rest_angle = float(c.attrib['rest_angle'])
            stiffness = float(c.attrib['stiffness'])
            damping = float(c.attrib['damping'])
            obj.cns[cname] = pymunk.DampedSpring(a, b, (a_a_x, a_a_y), (a_b_x, a_b_y), rest_angle,
                                                 stiffness, damping)

        elif cntype == 'RotaryLimitJoint':
            min = float(c.attrib['min'])
            max = float(c.attrib['max'])
            obj.cns[cname] = pymunk.RotaryLimitJoint(a, b, min, max)

        elif cntype == 'RatchetJoint':
            phase = float(c.attrib['phase'])
            ratchet = float(c.attrib['ratchet'])
            angle = float(c.attrib['angle'])
            obj.cns[cname] = pymunk.RatchetJoint(a, b, phase, ratchet)
            obj.cns[cname].angle = angle

        elif cntype == 'GearJoint':
            phase = float(c.attrib['phase'])
            ratio = float(c.attrib['ratio'])
            obj.cns[cname] = pymunk.GearJoint(a, b, phase, ratio)

        elif cntype == 'SimpleMotor':
            rate = float(c.attrib['rate'])
            obj.cns[cname] = pymunk.SimpleMotor(a, b, rate)

        space.add(obj.cns[cname])
        error_bias = float(c.attrib["error_bias"]) if c.attrib["error_bias"] != 'inf' else pymunk.inf
        max_bias = float(c.attrib["max_bias"]) if c.attrib["max_bias"] != 'inf' else pymunk.inf
        max_force = float(c.attrib["max_force"]) if c.attrib["max_force"] != 'inf' else pymunk.inf
        self_collide = int(c.attrib["collide_bodies"])
        obj.cns[cname].error_bias = error_bias
        obj.cns[cname].max_bias = max_bias
        obj.cns[cname].max_force = max_force
        obj.cns[cname].collide_bodies = self_collide


class Level:

    def __init__(self):
        self.bd = {}
        self.shp = {}
        self.cns = {}
        self.type = "level"
        self.player_x = 300
        self.player_y = 300

    def remove(self, space):
        for v in self.cns:
            space.remove(self.cns[v])
        for v in self.shp:
            space.remove(self.shp[v])
        for v in self.bd:
            space.remove(self.bd[v])

    def create(self, space):
        pass

        #PhysicsDumper().readData(path, space)
        #PhysicsDumper('level_4.xml', EXEC_FOLDER).dumpData(self)

    def draw(self, drawVectors=True, drawGraphics=True):

        if drawVectors:
            Util.drawVectors(self.shp)


# autogeometry level
# TODO [EH] join it with Level Class
class Level2:

    def __init__(self):
        self.bd = {}
        self.shp = {}
        self.cns = {}
        self.type = "autogeometry"
        self.t: Optional[arcade.Texture] = None
        self.segments = []
        self.density_x = 60
        self.density_y = 60
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
        self.t = None

    def create(self, space):
        #PhysicsDumper().readData(path, space)
        self.getMarchingCubes(self.density_x, self.density_y).sendSegmentsToPhysics(space)
        #PhysicsDumper('level_3.xml', EXEC_FOLDER).dumpData(self)

    def getTexture(self, path):
        self.t = arcade.load_texture(path)
        return self

    def getMarchingCubes(self, density_x: int, density_y: int):
        def segment_func(v0, v1):
            self.segments.append(((v0[0] * self.scale, v0[1] * self.scale),
                                  (v1[0] * self.scale, v1[1] * self.scale)))

        def sample_func(point):
            x = int(point.x)
            y = self.t.height - 1 - int(point.y)
            return self.t.image.getpixel((x, y))[3] / 255

        # TODO [EH] - add parameter whether march_soft or march_hard will be performed
        pymunk.autogeometry.march_soft(pymunk.BB(0, 0, self.t.width-1, self.t.height-1), density_x, density_y,
                                       self.alpha_threshold, segment_func, sample_func)

        return self

    def sendSegmentsToPhysics(self, space):
        # TODO [EH] change this body id into smthng else ?:P
        # TODO [EH] Should it be dumped to xml with texture setup?
        self.bd['new'] = pymunk.Body(1.0, 1.0, pymunk.Body.STATIC)
        space.add(self.bd['new'])
        for i in range(len(self.segments)):
            self.shp[str(i)] = pymunk.Segment(self.bd['new'], self.segments[i][0], self.segments[i][1], 1)
            space.add(self.shp[str(i)])
            self.shp[str(i)].friction = self.friction
            self.shp[str(i)].elasticity = self.elasticity

    def draw(self, drawVectors=True, drawGraphics=True):
        if drawGraphics:
            # TODO [EH] how to scale for nearest neighbour?
            arcade.draw_scaled_texture_rectangle(self.t.width*self.scale/2, self.t.height*self.scale/2, self.t, self.scale)
        if drawVectors:
            # seems faster than get all of the data from shape...
            # TODO [EH] needs to be profiled i guess
            for i in self.segments:
                arcade.draw_line(i[0][0], i[0][1], i[1][0], i[1][1], arcade.color.LEMON, 1)


class Vehicle:

    # TODO [EH] change this class into Vehicle

    def __init__(self):
        self.bd = {}
        self.shp = {}
        self.cns = {}
        self.bdTex = {}
        self.dir = 1  # TODO [EH] create some normal directions, now 1 is left wheel, -1 is right wheel
        self.prevDir = 1
        self.differential = False
        self.speed = 20
        self.acc_l = 0
        self.acc_r = 0

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
        #PhysicsDumper().readData(path, space)
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
        self.bdTex['lw'], self.bdTex['rw'] = self.bdTex['rw'], self.bdTex['lw']
        lshapes = self.bd['lw'].shapes
        rshapes = self.bd['rw'].shapes
        # TODO [EH] not good but works
        # TODO [EH] swap shapes, leave bodies as is. This needs to be changed (along with acceleration)
        for shape in lshapes:
            shape.space.remove(shape)
            shape.body = self.bd['rw']
            shape.space.add(shape)
        for shape in rshapes:
            shape.space.remove(shape)
            shape.body = self.bd['lw']
            shape.space.add(shape)
        # TODO [EH] Swap constraints and bodies

    def moveTo(self, x, y):
        for i in self.bd:
            self.bd[i].position += (x, y)

    def draw(self, drawVectors=True, drawGraphics=True):

        if self.dir != self.prevDir:
            self.acc_l = 0
            self.acc_r = 0
            self.flip()
            self.prevDir = self.dir

        if drawVectors:
            Util.drawVectors(self.shp)

        if drawGraphics:
            for body in sorted(self.bd.keys()):
                self.bdTex[body].set_position(self.bd[body].position.x, self.bd[body].position.y)
                self.bdTex[body].angle = self.bd[body].angle * 180 / math.pi
                self.bdTex[body].draw()

    def update(self, key = None):

        if key:
            if key.k[arcade.key.E]:
                self.differential = not self.differential
                key.unsetKey(arcade.key.E)

            if key.k[arcade.key.W]:
                if self.dir > 0:
                    curr_speed = -1.0 * self.speed
                    self.acc_l -= 0.05
                    if self.acc_l < curr_speed:
                        self.acc_l = curr_speed
                    self.bd['lw'].angular_velocity += self.acc_l
                    if self.bd['lw'].angular_velocity < curr_speed:
                        self.bd['lw'].angular_velocity = curr_speed
                    if self.differential:
                        self.acc_r -= 0.05
                        if self.acc_r < curr_speed:
                            self.acc_r = curr_speed
                        self.bd['rw'].angular_velocity += self.acc_r
                        if self.bd['rw'].angular_velocity < curr_speed:
                            self.bd['rw'].angular_velocity = curr_speed
                else:
                    curr_speed = self.speed
                    self.acc_r += 0.05
                    if self.acc_r > curr_speed:
                        self.acc_r = curr_speed
                    self.bd['rw'].angular_velocity += self.acc_r
                    if self.bd['rw'].angular_velocity > curr_speed:
                        self.bd['rw'].angular_velocity = curr_speed
                    if self.differential:
                        self.acc_l += 0.05
                        if self.acc_l > curr_speed:
                            self.acc_l = curr_speed
                        self.bd['lw'].angular_velocity += self.acc_l
                        if self.bd['lw'].angular_velocity > curr_speed:
                            self.bd['lw'].angular_velocity = curr_speed

            elif key.k[arcade.key.S]:
                if self.dir > 0:
                    curr_speed = self.speed / 3
                    self.acc_l += 0.02
                    if self.acc_l > curr_speed:
                        self.acc_l = curr_speed
                    self.bd['lw'].angular_velocity += self.acc_l
                    if self.bd['lw'].angular_velocity > curr_speed:
                        self.bd['lw'].angular_velocity = curr_speed
                    if self.differential:
                        self.acc_r += 0.02
                        if self.acc_r > curr_speed:
                            self.acc_r = curr_speed
                        self.bd['rw'].angular_velocity += self.acc_r
                        if self.bd['rw'].angular_velocity > curr_speed:
                            self.bd['rw'].angular_velocity = curr_speed
                else:
                    curr_speed = -1 * self.speed / 3
                    self.acc_r -= 0.02
                    if self.acc_r < curr_speed:
                        self.acc_r = curr_speed
                    self.bd['rw'].angular_velocity += self.acc_r
                    if self.bd['rw'].angular_velocity < curr_speed:
                        self.bd['rw'].angular_velocity = curr_speed
                    if self.differential:
                        self.acc_r -= 0.02
                        if self.acc_l < curr_speed:
                            self.acc_l = curr_speed
                        self.bd['lw'].angular_velocity += self.acc_l
                        if self.bd['lw'].angular_velocity < curr_speed:
                            self.bd['lw'].angular_velocity = curr_speed

            else:
                self.acc_l = 0
                self.acc_r = 0

            if key.k[arcade.key.D]:
                self.bd['head'].apply_force_at_local_point((2120, 0), (0, 30))
                self.bd['head'].apply_force_at_local_point((-2120, 0), (0, -30))
            if key.k[arcade.key.A]:
                self.bd['head'].apply_force_at_local_point((-2120, 0), (0, 30))
                self.bd['head'].apply_force_at_local_point((2120, 0), (0, -30))
            if key.k[arcade.key.SPACE]:
                self.dir *= -1

            key.unsetKey(arcade.key.SPACE)


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)



        self.space = None
        self.bike = None
        self.level = None
        self.key = Keys()
        self.ang_vel = 0
        self.music = None
        self.prevtime = time.time()
        self.munktime = time.time()
        self.update_time = 0
        self.set_update_rate(1/60)

        self.processPhysics = True
        self.printFPS = False
        self.drawGraphics = True
        self.drawVectors = False
        self.drawText = True
        self.printPhysicElems = False

        self.vehicles = Util.getAllEntityFiles(Util.getVehiclePath())
        self.levels = Util.getAllEntityFiles(Util.getLevelsPath())

        self.help = ''''W' and 'S' to steer, ' ' to change wheels,
'A' and 'D' to rotate, 'E' to lock/unlock differential,
'Z' to dump level and bike to xml, 'X' to hide text,
'C' to hide graphics, 'V' to ignore physics
'B' to reload bike, 'N' to reload level
'Q' to print FPS in console, 'M' to display vectors'''

        print(self.help)
        self.fn = EXEC_FOLDER + '\\Pacifico.ttf'
        self.cwd = "Current Working Dir = " + EXEC_FOLDER

    def setup(self):
        """ Set up the game here. Call this function to restart the game. """

        # TODO [EH] how does this work? Should 1 game have one Window? if yes, when to call this func (how load
        # new levels? Should main loop be stopped? :|

        self.space = pymunk.Space()
        self.space.gravity = (0, -100)
        self.space.damping = 1

        self.level = PhysicsDumper().readData(self.levels[self.levels[-1]], self.space)
        #self.level.create(self.levels[self.levels[-1]], self.space)
        self.bike = PhysicsDumper().readData(self.vehicles[self.vehicles[-1]], self.space)
        #self.bike.create(self.vehicles[self.vehicles[-1]], self.space)
        self.bike.moveTo(self.level.player_x, self.level.player_y)

        #PhysicsDumper('_level2.xml', EXEC_FOLDER).dumpData(self.level2)

        self.music = arcade.Sound(":resources:music/1918.mp3", streaming=True)
        self.music.play(0.02)

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

        self.level.draw(self.drawVectors, self.drawGraphics)
        self.bike.draw(self.drawVectors, self.drawGraphics)

        if self.drawText:
            arcade.draw_text(self.cwd, v[0] + 700, v[2] + 75, arcade.color.BLACK, 12, font_name=self.fn)
            arcade.draw_text(self.help, v[0] + 20, v[2] + 90, arcade.color.BLACK, 12, font_name=self.fn)

        if self.printFPS:
            dt = time.time() - self.prevtime
            dt = 0.001 if dt <= 0.001 else dt
            print("FPS---- " + str(1 / (dt)) + "fps")

        if self.printPhysicElems:
            self.print_physic_elems(self.bike.bd, 'rw')

        self.prevtime = t

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        # TODO [EH] handle car :P
        if key in self.key.k:
            self.key.setKey(key)

        # other stuff
        elif key == arcade.key.Z:
            PhysicsDumper().dumpData(EXEC_FOLDER + '\\test_dumps\\dump_bike.xml', self.bike)
            PhysicsDumper().dumpData(EXEC_FOLDER + '\\test_dumps\\dump_level.xml', self.level)
        elif key == arcade.key.X:
            self.drawText = not self.drawText
        elif key == arcade.key.C:
            self.drawGraphics = not self.drawGraphics
        elif key == arcade.key.V:
            self.processPhysics = not self.processPhysics
        elif key == arcade.key.B:
            self.bike.remove(self.space)
            self.bike = PhysicsDumper().readData(self.vehicles[self.vehicles[-1]], self.space)
            self.bike.moveTo(self.level.player_x, self.level.player_y)
        elif key == arcade.key.N:
            type = self.level.type[:]
            self.level.remove(self.space)
            del self.level
            self.level = PhysicsDumper().readData(Util.getNextEntity(self.levels), self.space)
        elif key == arcade.key.Q:
            self.printFPS = not self.printFPS
        elif key == arcade.key.M:
            self.drawVectors = not self.drawVectors
        elif key == arcade.key.ESCAPE:
            self.close()
        elif key == arcade.key.F:
            self.bike.remove(self.space)
            self.bike = PhysicsDumper().readData(Util.getNextEntity(self.vehicles), self.space)
            self.bike.moveTo(self.level.player_x, self.level.player_y)

    def on_key_release(self, key: int, modifiers: int):

        if key in self.key.k:
            self.key.unsetKey(key)

    def on_close(self):
        print("Closing this")
        self.close()

    def on_update(self, delta_time):
        """ Movement and game logic """
        t = time.time()
        self.update_time = delta_time

        self.bike.update(self.key)

        if self.processPhysics:
            self.space.step(1/60)

        # Do the view scrolling
        arcade.set_viewport(self.bike.bd['head'].position.x - SCREEN_WIDTH/2,
                            self.bike.bd['head'].position.x + SCREEN_WIDTH/2,
                            self.bike.bd['head'].position.y - SCREEN_HEIGHT/2,
                            self.bike.bd['head'].position.y + SCREEN_HEIGHT/2)

        self.munktime = time.time() - t


def main():
    """ Main method """
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    # correct execution working dir when frozen by pyinstaller
    if not sys.executable.endswith("python.exe"):
        EXEC_FOLDER = sys.executable[:sys.executable.rfind('\\')]
    if len(sys.argv) > 1:
        if sys.argv[1] == "-profile":
            cProfile.run("main()", "main_prof")
            pstats.Stats('main_prof').strip_dirs().sort_stats(pstats.SortKey.CUMULATIVE, pstats.SortKey.TIME).print_stats()
    else:
        main()

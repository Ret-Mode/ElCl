# file handling
import util
import svg_parser
import objects

import pymunk
import arcade
import PIL
import xml.etree.ElementTree as ET
# PyCharm type helper
from typing import Optional, Dict, List, Tuple, Any

# TODO [EH] move this to separate file
# TODO [EH] add defaults to unnecessary fields


# TODO [EH] - chop this even more?
def dumpData(path, obj, fullDump=False):
    root = ET.Element('root')
    root.set("type", obj.type)

    if obj.type == 'vehicle':
        root.set("speed", str(obj.speed))
        bodies = ET.SubElement(root, 'bodies')
        for b in obj.bd:
            dumpBodyWithTex(bodies, b, obj, fullDump)
    elif obj.type == 'autogeometry':
        dumpAutogeometry(root, obj, svgPath=path[:path.rfind('\\') + 1])
    elif obj.type == 'level':
        root.set("player_x", str(obj.player_x))
        root.set("player_y", str(obj.player_y))
        bodies = ET.SubElement(root, 'bodies')
        for b in obj.bd:
            dumpBody(bodies, b, obj, fullDump)
    else:
        bodies = ET.SubElement(root, 'bodies')
        for b in obj.bd:
            dumpBody(bodies, b, obj, fullDump)

    constraints = ET.SubElement(root, 'constraints')

    for c in obj.cns:
        dumpConstraints(constraints, c, obj, fullDump)

    # NOTE [EH] fix newlines
    xml_s = ET.tostring(root, encoding="unicode").replace('</root>', '\n</root>')
    for i in ['<bodies>', '</bodies>', '<bodies />', '<constraints>', '<constraints />', '</constraints>',
              '<svg_file ']:
        xml_s = xml_s.replace(i, '\n ' + i)
    for i in ['<body ', '</body>', '<body />', '<constraint ', '</constraint>', '<constraint /> ']:
        xml_s = xml_s.replace(i, '\n  ' + i)
    for i in ['<shape ', '</shape>', '<shape />']:
        xml_s = xml_s.replace(i, '\n   ' + i)

    f = open(path, "w")
    f.write(str(xml_s))
    f.close()


def dumpAutogeometry(rootElem: Optional[ET.Element], obj, fullDump=False, svgPath=None):
    texName: Optional[str] = obj.t.texture.name
    baseDir = util.getLevelsPath()
    if texName.startswith(baseDir):
        texName = texName[len(baseDir):texName.find('.png') + 4]
        if texName[0] == '\\' or texName[0] == '/':
            texName = texName[1:]

    space = None
    for i in obj.bd:
        space = obj.bd[i].space
    if space:
        rootElem.set("space_gravity", str(space.gravity[0]) + ' ' + str(space.gravity[1]))
        rootElem.set("space_damping", str(space.damping))
    rootElem.set("texture", texName)
    rootElem.set("autogeometry_dx", str(obj.autogeometry_dx))
    rootElem.set("autogeometry_dy", str(obj.autogeometry_dy))
    if obj.alpha_threshold != 0.5 or fullDump:
        rootElem.set("alpha_threshold", str(obj.alpha_threshold))
    if obj.scale != 1.0 or fullDump:
        rootElem.set("scale", str(obj.scale))
    if obj.elasticity != 0.0 or fullDump:
        rootElem.set("elasticity", str(obj.elasticity))
    if obj.friction != 0.0 or fullDump:
        rootElem.set("friction", str(obj.friction))
    if obj.radius != 1.0 or fullDump:
        rootElem.set("radius", str(obj.radius))

    rootElem.set("player_x", str(obj.player_x))
    rootElem.set("player_y", str(obj.player_y))

    svgElem: Optional[ET.SubElement] = ET.SubElement(rootElem, 'svg_file')
    svgElem.set('path', texName + ".svg")
    svg_parser.dumpSvg(svgPath if svgPath else baseDir, texName, obj.scale, obj.t.width, obj.t.height, obj.segments)


def dumpBodyWithTex(bodiesElem: Optional[ET.Element], b: str, obj, fullDump=False):
    body: Optional[pymunk.Body] = obj.bd[b]
    texName: Optional[str] = obj.bdTex[b].texture.name
    baseDir = util.EXEC_FOLDER
    xmlbody: Optional[ET.SubElement] = ET.SubElement(bodiesElem, 'body')

    # write to xml
    xmlbody.set("id", b)

    if body.body_type == pymunk.Body.DYNAMIC:
        xmlbody.set("type", "DYNAMIC")
    elif body.body_type == pymunk.Body.KINEMATIC:
        xmlbody.set("type", "KINEMATIC")
    elif fullDump:
        xmlbody.set("type", "STATIC")

    # TODO [EH] car related --> needs to be moved from here?
    if b in obj.motorParams:
        xmlbody.set("motor", "True")
        xmlbody.set("speed", str(obj.motorParams[b][0]))
        if obj.motorParams[b][1] != 0.05 or fullDump:
            xmlbody.set("acc", str(obj.motorParams[b][1]))
        xmlbody.set("differential_dest", " ".join(obj.differentialDest[b]))
    if b == obj.centralId:
        xmlbody.set("central", "True")
        if obj.rotational_force != 20.0:
            xmlbody.set("rotational_force", str(obj.rotational_force))
        if obj.rotational_limit != 2.0:
            xmlbody.set("rotational_limit", str(obj.rotational_limit))

    # setup textures
    if obj.type == 'vehicle':
        baseDir = util.getVehiclePath()
    elif obj.type == 'autogeometry' or obj.type == 'level':
        baseDir = util.getLevelsPath()
    if texName.startswith(baseDir):
        texName = texName[len(baseDir):texName.find('.png') + 4]
        if texName[0] == '\\' or texName[0] == '/':
            texName = texName[1:]

    xmlbody.set("texture", texName)
    if obj.bdTex[b].texture_rotation or fullDump:
        xmlbody.set("texture_flip_lr", "True")
    if obj.bdTex[b].scale != 1.0 or fullDump:
        xmlbody.set("texture_scale", str(obj.bdTex[b].scale))

    if body.mass != pymunk.inf or fullDump:
        xmlbody.set("mass", str(body.mass))
    if body.moment != pymunk.inf or fullDump:
        xmlbody.set("moment", str(body.moment))

    if body.position.x != 0.0 or body.position.y != 0 or fullDump:
        xmlbody.set("position_x", str(body.position.x))
        xmlbody.set("position_y", str(body.position.y))

    if body.angle != 0.0 or fullDump:
        xmlbody.set("start_angle", str(body.angle))

    for s in body.shapes:
        for shp in obj.shp:
            if obj.shp[shp] == s:
                dumpShape(xmlbody, shp, obj, fullDump)
                break


def dumpBody(bodiesElem: Optional[ET.Element], b: str, obj, fullDump=False):
    body: Optional[pymunk.Body] = obj.bd[b]
    xmlbody: Optional[ET.SubElement] = ET.SubElement(bodiesElem, 'body')

    xmlbody.set("id", b)

    if body.body_type == pymunk.Body.DYNAMIC:
        xmlbody.set("type", "DYNAMIC")
    elif body.body_type == pymunk.Body.KINEMATIC:
        xmlbody.set("type", "KINEMATIC")
    elif fullDump:
        xmlbody.set("type", "STATIC")

    if body.mass != pymunk.inf or fullDump:
        xmlbody.set("mass", str(body.mass))
    if body.moment != pymunk.inf or fullDump:
        xmlbody.set("moment", str(body.moment))
    if body.position.x != 0.0 or body.position.y != 0 or fullDump:
        xmlbody.set("position_x", str(body.position.x))
        xmlbody.set("position_y", str(body.position.y))

    if body.angle != 0.0 or fullDump:
        xmlbody.set("start_angle", str(body.angle))

    for s in body.shapes:
        for shp in obj.shp:
            if obj.shp[shp] == s:
                dumpShape(xmlbody, shp, obj, fullDump)
                break


def dumpShape(bodyElement, shp, obj, fullDump=False):
    s = obj.shp[shp]
    xmlshape = ET.SubElement(bodyElement, 'shape')
    xmlshape.set("id", shp)

    if s.__class__.__name__ == "Segment":
        xmlshape.set("type", 'SEGMENT')
        xmlshape.set("a_x", str(s.a[0]))
        xmlshape.set("a_y", str(s.a[1]))
        xmlshape.set("b_x", str(s.b[0]))
        xmlshape.set("b_y", str(s.b[1]))

    elif s.__class__.__name__ == "Poly":
        xmlshape.set("type", "POLY")
        v = s.get_vertices()
        polyTxt = " ".join(str(i.x) + " " + str(i.y) for i in v)
        xmlshape.text = polyTxt

    elif s.__class__.__name__ == "Circle":
        xmlshape.set("type", 'CIRCLE')
        xmlshape.set("offset_x", str(s.offset.x))
        xmlshape.set("offset_y", str(s.offset.y))

    if s.elasticity != 0.0 or fullDump:
        xmlshape.set("elasticity", str(s.elasticity))
    if s.friction != 0.0 or fullDump:
        xmlshape.set("friction", str(s.friction))
    if s.radius != 1.0 or fullDump:
        xmlshape.set("radius", str(s.radius))
    if s.density != 0.0 or fullDump:
        xmlshape.set("density", str(s.density))

    filter = s.filter
    if filter.group != 0:
        xmlshape.set("collision_group", str(filter.group))
    if filter.categories != 0b11111111111111111111111111111111:
        xmlshape.set("collision_category", str(bin(filter.category)))
    if filter.mask != 0b11111111111111111111111111111111:
        xmlshape.set("collision_mask", str(bin(filter.mask)))


def dumpConstraints(constraintsElement, c, obj, fullDump=False):
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

    if cns.__class__.__name__ == "PinJoint":
        constraint.set("type", "PinJoint")
        constraint.set("a", ba)
        constraint.set("b", bb)
        constraint.set("anchor_a_x", str(cns.anchor_a[0]))
        constraint.set("anchor_a_y", str(cns.anchor_a[1]))
        constraint.set("anchor_b_x", str(cns.anchor_b[0]))
        constraint.set("anchor_b_y", str(cns.anchor_b[1]))
        constraint.set("distance", str(cns.distance))

    elif cns.__class__.__name__ == "SlideJoint":
        constraint.set("type", "SlideJoint")
        constraint.set("a", ba)
        constraint.set("b", bb)
        constraint.set("anchor_a_x", str(cns.anchor_a[0]))
        constraint.set("anchor_a_y", str(cns.anchor_a[1]))
        constraint.set("anchor_b_x", str(cns.anchor_b[0]))
        constraint.set("anchor_b_y", str(cns.anchor_b[1]))
        constraint.set("max", str(cns.max))
        constraint.set("min", str(cns.min))

    elif cns.__class__.__name__ == "PivotJoint":
        constraint.set("type", "PivotJoint")
        constraint.set("a", ba)
        constraint.set("b", bb)
        constraint.set("anchor_a_x", str(cns.anchor_a[0]))
        constraint.set("anchor_a_y", str(cns.anchor_a[1]))
        constraint.set("anchor_b_x", str(cns.anchor_b[0]))
        constraint.set("anchor_b_y", str(cns.anchor_b[1]))

    elif cns.__class__.__name__ == "GrooveJoint":
        constraint.set("type", "GrooveJoint")
        constraint.set("a", ba)
        constraint.set("b", bb)
        constraint.set("groove_a_x", str(cns.groove_a[0]))
        constraint.set("groove_a_y", str(cns.groove_a[1]))
        constraint.set("groove_b_x", str(cns.groove_b[0]))
        constraint.set("groove_b_y", str(cns.groove_b[1]))
        constraint.set("anchor_b_x", str(cns.anchor_b[0]))
        constraint.set("anchor_b_y", str(cns.anchor_b[1]))

    elif cns.__class__.__name__ == "DampedSpring":
        constraint.set("type", "DampedSpring")
        constraint.set("a", ba)
        constraint.set("b", bb)
        constraint.set("anchor_a_x", str(cns.anchor_a[0]))
        constraint.set("anchor_a_y", str(cns.anchor_a[1]))
        constraint.set("anchor_b_x", str(cns.anchor_b[0]))
        constraint.set("anchor_b_y", str(cns.anchor_b[1]))
        constraint.set("rest_length", str(cns.rest_length))
        constraint.set("stiffness", str(cns.stiffness))
        constraint.set("damping", str(cns.damping))

    elif cns.__class__.__name__ == "DampedRotarySpring":
        constraint.set("type", "DampedRotarySpring")
        constraint.set("a", ba)
        constraint.set("b", bb)
        constraint.set("rest_angle", str(cns.rest_angle))
        constraint.set("stiffness", str(cns.stiffness))
        constraint.set("damping", str(cns.damping))

    elif cns.__class__.__name__ == "RotaryLimitJoint":
        constraint.set("type", "RotaryLimitJoint")
        constraint.set("a", ba)
        constraint.set("b", bb)
        constraint.set("max", str(cns.max))
        constraint.set("min", str(cns.min))

    elif cns.__class__.__name__ == "RatchetJoint":
        constraint.set("type", "RatchetJoint")
        constraint.set("a", ba)
        constraint.set("b", bb)
        constraint.set("phase", str(cns.phase))
        constraint.set("ratchet", str(cns.ratchet))
        constraint.set("angle", str(cns.angle))

    elif cns.__class__.__name__ == "GearJoint":
        constraint.set("type", "GearJoint")
        constraint.set("a", ba)
        constraint.set("b", bb)
        constraint.set("phase", str(cns.phase))
        constraint.set("ratio", str(cns.ratio))

    elif cns.__class__.__name__ == "SimpleMotor":
        constraint.set("a", ba)
        constraint.set("b", bb)
        constraint.set("type", "SimpleMotor")
        constraint.set("rate", str(cns.rate))

    # TODO [EH] not obligatory data
    if cns.collide_bodies == 1 or fullDump:
        constraint.set("collide_bodies", str(cns.collide_bodies))

    if str(cns.error_bias) != "0.0017970074436457143" or fullDump:
        constraint.set("error_bias", str(cns.error_bias))

    if cns.max_bias != pymunk.inf or fullDump:
        constraint.set("max_bias", str(cns.max_bias))

    if cns.max_force != pymunk.inf or fullDump:
        constraint.set("max_force", str(cns.max_force))


def readData(path, space: pymunk.Space):
    tree = ET.parse(path)
    root = tree.getroot()
    obj = None
    if 'type' in root.attrib:

        if root.attrib["type"] == 'autogeometry':
            # damn, swapped obj and path args :(
            obj = objects.Level2()
            obj.type = root.attrib["type"]
            obj.src = "svg"
            readAutogeometry(root, obj, path)
            if len(obj.segments) == 0:
                print("Physics data not found in svg. Fallback to autogeometry.")
                obj.src = "cubes"
                obj.getMarchingCubes(obj.autogeometry_dx, obj.autogeometry_dy)
            obj.sendSegmentsToPhysics(space)

            if 'space_gravity' in root.attrib:
                x, y = root.attrib['space_gravity'].split()
                space.gravity = (float(x), float(y))
            if 'space_damping' in root.attrib:
                space.damping = float(root.attrib['space_damping'])

            obj.enemiesToLoad = readEnemies(root)

            return obj

        elif root.attrib["type"] == 'level':
            obj = objects.Level()
            obj.type = root.attrib["type"]
            obj.player_x = float(root.attrib["player_x"])
            obj.player_y = float(root.attrib["player_y"])

        elif root.attrib["type"] == 'vehicle':
            obj = objects.Vehicle()
            obj.type = root.attrib["type"]

        elif root.attrib["type"] == 'enemy':
            obj = objects.Enemy()
            obj.type = root.attrib["type"]

        else:
            obj = objects.Level()
            obj.type = 'level'

    for child in root:
        if child.tag == 'bodies':
            for body in child:
                if 'texture' in body.attrib:
                    # damn, swapped obj and path args :(
                    readBodyWithTex(body, obj, space, path)
                else:
                    readBody(body, obj, space)

    for child in root:
        if child.tag == 'constraints':
            for c in child:
                readConstraint(c, obj, space)

    return obj


def readEnemies(root: Optional[ET.Element]) -> List[Tuple[float, float]]:
    enemies = []
    for child in root:
        if child.tag == 'enemies':
            for enemy in child:
                x, y = enemy.attrib['position'].split()
                enemies.append((float(x), float(y)))
    return enemies


def readAutogeometry(root: Optional[ET.Element], obj, path: str):
    obj.scale = float(root.attrib["scale"]) if "scale" in root.attrib else 1.0
    obj.t = arcade.sprite.Sprite(util.getFileFromOtherFilePath(path, root.attrib["texture"]),
                                 obj.scale)
    # obj.t._sprite_list = arcade.sprite_list.SpriteList()
    # obj.t._sprite_list.append(obj.t)
    obj.t.draw()
    obj.t.position = obj.t.width / 2, obj.t.height / 2
    obj.autogeometry_dx = int(root.attrib["autogeometry_dx"])
    obj.autogeometry_dy = int(root.attrib["autogeometry_dy"])

    obj.alpha_threshold = float(root.attrib["alpha_threshold"]) if "alpha_threshold" in root.attrib else 0.5
    obj.friction = float(root.attrib["friction"]) if "friction" in root.attrib else 0.0
    obj.elasticity = float(root.attrib["elasticity"]) if "elasticity" in root.attrib else 0.0
    obj.radius = float(root.attrib["radius"]) if "radius" in root.attrib else 1.0

    obj.player_x = float(root.attrib["player_x"])
    obj.player_y = float(root.attrib["player_y"])

    for child in root:
        if child.tag == 'svg_file':
            obj.segments = svg_parser.readSvg(util.getFileFromOtherFilePath(path, child.attrib["path"]), obj.scale)


def readBodyWithTex(body, obj, space, path: str):
    type = body.attrib['type']
    if type == 'DYNAMIC':
        type = pymunk.Body.DYNAMIC
    elif type == "KINEMATIC":
        type = pymunk.Body.KINEMATIC
    else:
        type = pymunk.Body.STATIC

    # read from xml
    name = body.attrib["id"]
    mass = pymunk.inf
    moment = pymunk.inf
    px = 0.0
    py = 0.0
    scale = 1.0
    angle = 0.0
    texRot = True

    if "mass" in body.attrib:
        mass = float(body.attrib["mass"])

    # TODO [EH] calc moment when not given
    if "moment" in body.attrib:
        moment = float(body.attrib["moment"])

    if "position_x" in body.attrib and "position_y" in body.attrib:
        px = float(body.attrib["position_x"])
        py = float(body.attrib["position_y"])

    if 'position' in body.attrib:
        tmp = body.attrib["position_x"].split()
        px = float(tmp[0])
        py = float(tmp[1])

    if "start_angle" in body.attrib:
        angle = float(body.attrib["start_angle"])

    obj.bd[name] = pymunk.Body(mass, moment, type)
    space.add(obj.bd[name])
    obj.bd[name].position = px, py
    obj.bd[name].angle = angle
    obj.bd[name].master = obj


    if 'texture_scale' in body.attrib:
        scale = float(body.attrib['texture_scale'])
    # obj.bdTex[name]: arcade.sprite.Sprite = arcade.sprite.Sprite(Util.getFileFromOtherFilePath(path, body.attrib["texture"]), scale)
    obj.bdTex[name]: arcade.sprite.Sprite = arcade.sprite.Sprite()
    obj.bdTex[name].texture = arcade.Texture(name, PIL.Image.open(
        util.getFileFromOtherFilePath(path, body.attrib["texture"])).convert('RGBA'))
    obj.bdTex[name].scale = scale
    # draw to generate sprite list and vbo for the sprite/image
    obj.bdTex[name].draw()
    # obj.bdTex[name]._sprite_list = arcade.sprite_list.SpriteList()
    # obj.bdTex[name]._sprite_list.append(obj.bdTex[name])
    if "texture_flip_lr" in body.attrib:
        texRot = body.attrib["texture_flip_lr"]
    obj.bdTex[name].texture_rotation = True if texRot == 'True' else False

    # obj.bdTex[name].scale = scale
    # obj.bdTex[name].texture_transform.scale(obj.bdTex[name].texture_scale_x, obj.bdTex[name].texture_scale_y)

    # TODO [EH] car related params --> needs to be moved from here?
    if 'motor' in body.attrib and 'speed' in body.attrib:
        acc = 0.05
        if 'acc' in body.attrib:
            acc = float(body.attrib['acc'])
        obj.motorParams[name] = [float(body.attrib['speed']), acc, 0.0]
        if "differential_dest" in body.attrib:
            obj.differentialDest[name] = body.attrib['differential_dest'].split()

    if 'central' in body.attrib and body.attrib['central'] == "True":
        obj.centralId = name
        obj.startAngle = angle
        obj.rotational_force = 20.0
        obj.rotational_limit = 2.0
        if "rotational_force" in body.attrib:
            obj.rotational_force = float(body.attrib['rotational_force'])
        if "rotational_limit" in body.attrib:
            obj.rotational_limit = float(body.attrib['rotational_limit'])

    for shape in body:
        if shape.tag == 'shape':
            readShape(shape, obj.bd[name], obj, space)


def readBody(body, obj, space):
    type = body.attrib['type']
    if type == 'DYNAMIC':
        type = pymunk.Body.DYNAMIC
    elif type == "KINEMATIC":
        type = pymunk.Body.KINEMATIC
    else:
        type = pymunk.Body.STATIC

    name = body.attrib["id"]
    mass = pymunk.inf
    moment = pymunk.inf
    px = 0.0
    py = 0.0
    angle = 0.0

    if "mass" in body.attrib:
        mass = float(body.attrib["mass"])

    # TODO [EH] calc moment when not given
    if "moment" in body.attrib:
        moment = float(body.attrib["moment"])

    if "position_x" in body.attrib and "position_y" in body.attrib:
        px = float(body.attrib["position_x"])
        py = float(body.attrib["position_y"])

    if 'position' in body.attrib:
        tmp = body.attrib["position_x"].split()
        px = float(tmp[0])
        py = float(tmp[1])

    if "start_angle" in body.attrib:
        angle = float(body.attrib["start_angle"])

    obj.bd[name] = pymunk.Body(mass, moment, type)
    space.add(obj.bd[name])
    obj.bd[name].position = px, py
    obj.bd[name].angle = angle
    obj.bd[name].master = obj

    for shape in body:
        if shape.tag == 'shape':
            readShape(shape, obj.bd[name], obj, space)


def readShape(shape, body, obj, space):
    stype = shape.attrib['type']
    sname = shape.attrib["id"]

    elasticity = 0.0
    friction = 0.0
    density = 0.0
    radius = 1.0

    if 'elasticity' in shape.attrib:
        elasticity = float(shape.attrib["elasticity"])
    if 'friction' in shape.attrib:
        friction = float(shape.attrib["friction"])
    if 'density' in shape.attrib:
        density = float(shape.attrib["density"])
    if 'radius' in shape.attrib:
        radius = float(shape.attrib["radius"])

    if stype == "SEGMENT":
        # TODO[EH]: change to ab='1 2 3 4'
        a_x = float(shape.attrib["a_x"])  # + px
        a_y = float(shape.attrib["a_y"])  # + py
        b_x = float(shape.attrib["b_x"])  # + px
        b_y = float(shape.attrib["b_y"])  # + py
        obj.shp[sname] = pymunk.Segment(body, (a_x, a_y), (b_x, b_y), radius)
        space.add(obj.shp[sname])

    elif stype == "CIRCLE":
        # TODO[EH]: change to offset='1 2'
        o_x = float(shape.attrib["offset_x"])
        o_y = float(shape.attrib["offset_y"])
        obj.shp[sname] = pymunk.Circle(body, radius, (o_x, o_y))
        space.add(obj.shp[sname])

    elif stype == "POLY":
        verts = shape.text.split()
        tmp = [(float(verts[i]), float(verts[i + 1])) for i in range(0, len(verts), 2)]
        obj.shp[sname] = pymunk.Poly(body, tmp, None, radius)
        space.add(obj.shp[sname])

    else:
        print("ERROR - Didn't created any shape due to wrong shape type")

    obj.shp[sname].friction = friction
    obj.shp[sname].elasticity = elasticity
    if density > 0.0:
        obj.shp[sname].density = density

    f_group = 0
    f_category = 0b11111111111111111111111111111111
    f_mask = 0b11111111111111111111111111111111

    if 'collision_group' in shape.attrib:
        f_group = int(shape.attrib["collision_group"])
    if "collision_category" in shape.attrib:
        f_category = int(shape.attrib["collision_category"], 2)
    if "collision_mask" in shape.attrib:
        f_mask = int(shape.attrib["collision_mask"], 2)

    obj.shp[sname].filter = pymunk.ShapeFilter(f_group, f_category, f_mask)

    if "collision_type" in shape.attrib:
        obj.shp[sname].collision_type = int(shape.attrib["collision_type"])

    obj.shp[sname].master = obj

def readConstraint(c, obj, space):
    cntype = c.attrib['type']
    cname = c.attrib['id']
    a = obj.bd[c.attrib['a']]
    b = obj.bd[c.attrib['b']]

    if cntype == 'PinJoint':
        a_a_x = float(c.attrib['anchor_a_x'])
        a_a_y = float(c.attrib['anchor_a_y'])
        a_b_x = float(c.attrib['anchor_b_x'])
        a_b_y = float(c.attrib['anchor_b_y'])
        obj.cns[cname] = pymunk.PinJoint(a, b, (a_a_x, a_a_y), (a_b_x, a_b_y))
        if 'distance' in c.attrib:
            distance = float(c.attrib['distance'])
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
        rest_angle = float(c.attrib['rest_angle'])
        stiffness = float(c.attrib['stiffness'])
        damping = float(c.attrib['damping'])
        obj.cns[cname] = pymunk.DampedRotarySpring(a, b, rest_angle,
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

    self_collide = 0
    if "collide_bodies" in c.attrib:
        self_collide = int(c.attrib["collide_bodies"])

    obj.cns[cname].collide_bodies = self_collide

    if "error_bias" in c.attrib:
        error_bias = float(c.attrib["error_bias"])
        obj.cns[cname].error_bias = error_bias

    if "max_bias" in c.attrib:
        max_bias = float(c.attrib["max_bias"]) if c.attrib["max_bias"] != 'inf' else pymunk.inf
        obj.cns[cname].max_bias = max_bias

    if "max_force" in c.attrib:
        max_force = float(c.attrib["max_force"]) if c.attrib["max_force"] != 'inf' else pymunk.inf
        obj.cns[cname].max_force = max_force

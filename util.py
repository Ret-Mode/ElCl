import os
import math
import arcade
import pymunk


EXEC_FOLDER: str


def setupExecFolder(fullPath: str):
    global EXEC_FOLDER
    EXEC_FOLDER = fullPath


def drawVectors(shapeDict):
    for s in shapeDict:
        shape = shapeDict[s]
        if shape.__class__.__name__ == "Poly":
            bpos = shape.body.position
            poly = shape.get_vertices()
            for v in range(len(poly) - 1):
                x, y = poly[v].rotated(shape.body.angle) + bpos
                x2, y2 = poly[v + 1].rotated(shape.body.angle) + bpos
                arcade.draw_line(x, y, x2, y2, arcade.color.BLACK, 1)
            x, y = poly[-1].rotated(shape.body.angle) + bpos
            x2, y2 = poly[0].rotated(shape.body.angle) + bpos
            arcade.draw_line(x, y, x2, y2, arcade.color.BLACK, 1)
        elif shape.__class__.__name__ == "Segment":
            bpos = shape.body.position
            x, y = shape.a.rotated(shape.body.angle) + bpos
            x2, y2 = shape.b.rotated(shape.body.angle) + bpos
            arcade.draw_line(x, y, x2, y2,
                             arcade.color.YELLOW, 1)
        elif shape.__class__.__name__ == "Circle":
            bpos = shape.body.position
            arcade.draw_circle_filled(bpos[0], bpos[1], shape.radius,
                                      arcade.color.GREEN, 1)


# TODO [EH] add conditions for name/extension
def getAllEntityFiles(path):
    output = []
    filesList = os.listdir(path)
    for f in filesList:
        if f.endswith(".xml"):
            output.append(path + f)
    return output


def getVehiclePath():
    return EXEC_FOLDER + '\\vehicles\\'


def getLevelsPath():
    return EXEC_FOLDER + '\\levels\\'


def getEnemiesPath():
    return EXEC_FOLDER + '\\enemies\\'


def getFolderFromFilePath(filePath):
    return filePath[:filePath.rfind('\\')]


def getFileFromOtherFilePath(filePath, file):
    return getFolderFromFilePath(filePath) + '\\' + file


def flipConstraints(cnsDict, mainBody, angleCorrection: float):
    # TODO [EH] now just one pass of update (chains like objects will end up crappy, byt we don't
    # TODO [EH] use them yet
    bodiesToFlip = []
    mainBody.angle -= angleCorrection
    for cnsId, cnsInternals in cnsDict.items():
        space = cnsInternals.a.space

        if cnsInternals.__class__.__name__ in ["PinJoint", "SlideJoint", "PivotJoint", "DampedSpring"]:
            # a: pymunk.Body = cnsInternals.a
            # b: pymunk.Body = cnsInternals.b
            space.remove(cnsInternals)
            cnsInternals.anchor_b = (-cnsInternals.anchor_b.x, cnsInternals.anchor_b.y)
            cnsInternals.anchor_a = (-cnsInternals.anchor_a.x, cnsInternals.anchor_a.y)
            space.add(cnsInternals)
            if cnsInternals.b not in bodiesToFlip:
                bodiesToFlip.append(cnsInternals.b)
        elif cnsInternals.__class__.__name__ == "GrooveJoint":
            space.remove(cnsInternals)
            cnsInternals.anchor_b = (-cnsInternals.anchor_b.x, cnsInternals.anchor_b.y)
            cnsInternals.groove_a = (-cnsInternals.groove_a.x, cnsInternals.groove_a.y)
            cnsInternals.groove_b = (-cnsInternals.groove_b.x, cnsInternals.groove_b.y)
            space.add(cnsInternals)
            if cnsInternals.b not in bodiesToFlip:
                bodiesToFlip.append(cnsInternals.b)

    for bodyToFlip in bodiesToFlip:
        vel = bodyToFlip.velocity - mainBody.velocity
        # space.remove(bodyToFlip)

        dest = bodyToFlip.position - mainBody.position
        dest.rotate(-mainBody.angle)
        at = math.atan2(dest.x, dest.y)
        dest.x *= -1
        dest.rotate(mainBody.angle)
        bodyToFlip.position = dest + mainBody.position
        vel.rotate(2 * at)
        bodyToFlip.velocity = mainBody.velocity + vel
        # space.add(bodyToFlip)
    mainBody.angle -= angleCorrection

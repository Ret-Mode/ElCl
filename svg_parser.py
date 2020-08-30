# file handling
import xml.etree.ElementTree as ET

# PyCharm type helper
from typing import List, Tuple, Any, Union

# there could be multiple paths in the file.
# also - why other segments does not work?

svg_format = """<svg
   xmlns="http://www.w3.org/2000/svg"
   xmlns:xlink="http://www.w3.org/1999/xlink"
   xmlns:el="EL"
   height="{i_height}px"
   width="{i_width}px"
   id="svg5">
   <el:start
      x="300"
      y="300" />
   <image
      xlink:href="{f_path}"
      y="0"
      x="0"
      width="{i_width}"
      height="{i_height}"
       style="image-rendering:optimizeSpeed"
       id="image1" />
{paths}</svg>"""

svg_paths = '''   <path
      style="fill:none;stroke:#000000;stroke-width:1.00631px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
      d="{xy_delta}"
      id="shape_{shape_id}" />
'''


def readImages(node, imageList):
    for element in node:
        if element.tag.endswith('}g') or element.tag == 'g':
            readImages(element, imageList)
        if element.tag.endswith('}image') or element.tag == 'image':

            imageList.append({'path': element.attrib['{http://www.w3.org/1999/xlink}href'],
                              'x': float(element.attrib['x']),
                              'y': float(element.attrib['y']),
                              'width': float(element.attrib['width']),
                              'height': float(element.attrib['height'])})


def readSegments(node, scale, height, segmentList):
    for polys in node:
        if polys.tag.endswith('}g') or polys.tag == 'g':
            readSegments(polys, scale, height, segmentList)
        elif polys.tag.endswith('}path') or polys.tag == 'path':
            segments = []
            text: List[str] = polys.attrib['d'].split()
            mode = 'm'
            px, py = 0.0, height
            x, y = 0.0, 0.0
            i = 0
            # TODO [EH] for compatibility with marching cubes, stores same point twice :/
            while i < len(text):
                if len(text[i]) == 1:
                    mode = text[i]
                else:
                    if mode == 'm':
                        x, y = text[i].split(",")
                        px, py = float(x) + px, py - float(y)
                    elif mode == 'M':
                        x, y = text[i].split(",")
                        px, py = float(x), height - float(y)
                    else:
                        if mode == 'v':
                            y = text[i]
                            x, y = px, py - float(y)
                        elif mode == 'V':
                            y = text[i]
                            x, y = px, height - float(y)
                        elif mode == 'h':
                            x = text[i]
                            x, y = px + float(x), py
                        elif mode == 'H':
                            x = text[i]
                            x, y = float(x), py
                        elif mode == 'l' or mode == 't':
                            x, y = text[i].split(',')
                            x, y = px + float(x), py - float(y)
                        elif mode == 'L' or mode == 'T':
                            x, y = text[i].split(',')
                            x, y = float(x), height - float(y)
                        elif mode == 'c':
                            i += 2
                            x, y = text[i].split(',')
                            x, y = px + float(x), py - float(y)
                        elif mode == 'C':
                            i += 2
                            x, y = text[i].split(',')
                            x, y = float(x), height - float(y)
                        elif mode == 's' or mode == 'q':
                            i += 1
                            x, y = text[i].split(',')
                            x, y = px + float(x), py - float(y)
                        elif mode == 'S' or mode == 'Q':
                            i += 1
                            x, y = text[i].split(',')
                            x, y = float(x), height - float(y)
                        elif mode == 'a':
                            i += 5
                            x, y = text[i].split(',')
                            x, y = px + float(x), py - float(y)
                        elif mode == 'A':
                            i += 5
                            x, y = text[i].split(',')
                            x, y = float(x), height - float(y)
                        seg1 = (scale * px, scale * py)
                        seg2 = (scale * x,  scale * y)
                        segments.append((seg1, seg2))
                        px, py = x, y
                    if mode == 'm':
                        mode = 'l'
                    elif mode == 'M':
                        mode = 'L'
                i += 1

            if mode == 'z' or mode == 'Z':
                seg1 = (scale * px, scale * py)
                seg2 = (segments[0][0][0],  segments[0][0][1])
                segments.append((seg1, seg2))
            segmentList.append(segments)


def readSvg(path: str, scale: float) -> List[List[Union[
    Tuple[Tuple[Union[float, Any], Union[float, Any]], Tuple[Union[float, Any], Union[float, Any]]], Tuple[
        Tuple[Union[float, Any], Union[float, Any]], Tuple[Any, Any]]]]]:
    height: float = 0
    segmentList = []
    imageList = []
    tree: ET = ET.parse(path)
    root: ET.Element = tree.getroot()

    readImages(root, imageList)

    if len(imageList) > 0:
        height = imageList[0]['height']

    readSegments(root, scale, height, segmentList)

    return segmentList


def dumpSvg(destPath: str, texture: str, scale: float, imgWidth, imgHeight, segmentsScaled: List[Tuple[Tuple[Tuple[float, float], Tuple[float, float]]]]):
    fileName = destPath + texture + ".svg"

    paths = ''
    shapeId = 1
    for segment in segmentsScaled:
        deltas = 'm ' + str(segment[0][0][0]/scale) + ',' + str(imgHeight - (segment[0][0][1])/scale)
        for i in segment:
            deltas = deltas + ' ' + str((i[1][0] - i[0][0])/scale) + ',' + str((i[0][1] - i[1][1])/scale)
        paths += svg_paths.format(xy_delta=deltas, shape_id=shapeId)
        shapeId += 1
    with open(fileName, "w") as svgFile:
        svgFile.write(svg_format.format(i_height=imgHeight, i_width=imgWidth, f_path=texture, paths=paths))


if __name__ == "__main__":
    readSvg("levels\\map_edits.svg",1.0)
    dumpSvg("tmp.png",3.0,2,256*3,[((1.41435954, 552.044841), (44.212212, 602.689161)), ((44.212212, 602.689161), (91.933692, 634.533678)), ((91.933692, 634.533678), (140.412672, 655.6354680000001)), ((140.412672, 655.6354680000001), (173.363532, 665.9945070000001)), ((173.363532, 665.9945070000001), (183.58930199999998, 658.32114)), ((183.58930199999998, 658.32114), (159.34987199999998, 633.382659)), ((159.34987199999998, 633.382659), (105.18964199999999, 568.5425910000001)), ((105.18964199999999, 568.5425910000001), (88.14634199999998, 531.7103910000001)), ((88.14634199999998, 531.7103910000001), (84.35890199999999, 486.821121)), ((84.35890199999999, 486.821121), (88.52509199999997, 445.7685600000001)), ((88.52509199999997, 445.7685600000001), (97.23628199999999, 430.4217900000001)), ((97.23628199999999, 430.4217900000001), (110.87098199999998, 426.2014500000001)), ((110.87098199999998, 426.2014500000001), (115.794702, 419.2954200000001)), ((115.794702, 419.2954200000001), (118.06702200000001, 394.74060000000014)), ((118.06702200000001, 394.74060000000014), (127.15675200000001, 372.8714700000001)), ((127.15675200000001, 372.8714700000001), (155.183652, 360.2103900000001)), ((155.183652, 360.2103900000001), (186.619482, 349.8513600000001)), ((186.619482, 349.8513600000001), (207.07147200000003, 352.15335000000005)), ((207.07147200000003, 352.15335000000005), (254.792952, 370.18578)), ((254.792952, 370.18578), (276.759942, 379.0101900000001)), ((276.759942, 379.0101900000001), (287.364702, 380.1612)), ((287.364702, 380.1612), (296.454642, 372.4878000000001)), ((296.454642, 372.4878000000001), (307.43817, 353.3043600000001)), ((307.43817, 353.3043600000001), (329.40518999999995, 338.7249600000001)), ((329.40518999999995, 338.7249600000001), (362.73456, 329.90055000000007)), ((362.73456, 329.90055000000007), (382.42926, 331.05156000000005)), ((382.42926, 331.05156000000005), (415.3797599999999, 314.1701700000001)), ((415.3797599999999, 314.1701700000001), (443.02779, 293.06835000000007)), ((443.02779, 293.06835000000007), (464.23751999999996, 285.77862000000005)), ((464.23751999999996, 285.77862000000005), (482.79594, 278.87259000000006)), ((482.79594, 278.87259000000006), (500.97549, 280.40727000000004)), ((500.97549, 280.40727000000004), (540.36477, 296.1377100000001)), ((540.36477, 296.1377100000001), (583.40286, 325.6641900000001)), ((583.40286, 325.6641900000001), (593.57988, 333.26046000000014)), ((593.57988, 333.26046000000014), (602.95323, 330.8188200000001)), ((602.95323, 330.8188200000001), (616.34385, 322.95123000000007)), ((616.34385, 322.95123000000007), (636.42966, 320.5095600000001)), ((636.42966, 320.5095600000001), (656.51535, 324.03642000000013)), ((656.51535, 324.03642000000013), (675.2622, 332.98914000000013)), ((675.2622, 332.98914000000013), (697.22298, 361.7464200000001)), ((697.22298, 361.7464200000001), (707.3995199999999, 390.2323800000001)), ((707.3995199999999, 390.2323800000001), (713.82717, 395.1156900000001)), ((713.82717, 395.1156900000001), (791.0921699999999, 399.3446400000001)), ((791.0921699999999, 399.3446400000001), (796.58388, 397.80996000000005)), ((796.58388, 397.80996000000005), (803.2118399999999, 387.45090000000005)), ((803.2118399999999, 387.45090000000005), (813.62727, 386.49174000000005)), ((813.62727, 386.49174000000005), (827.83014, 387.6427800000001)), ((827.83014, 387.6427800000001), (832.37502, 385.91628000000003)), ((832.37502, 385.91628000000003), (838.6244399999999, 379.96938)), ((838.6244399999999, 379.96938), (847.1459699999999, 375.74904000000004)), ((847.1459699999999, 375.74904000000004), (862.8638699999999, 376.1327100000001)), ((862.8638699999999, 376.1327100000001), (881.2327499999999, 378.24291000000005)), ((881.2327499999999, 378.24291000000005), (900.7380299999999, 386.87544)), ((900.7380299999999, 386.87544), (917.7814199999998, 403.56507)), ((917.7814199999998, 403.56507), (927.4395599999998, 410.08740000000006)), ((927.4395599999998, 410.08740000000006), (958.8750299999999, 426.20151)), ((958.8750299999999, 426.20151), (984.25074, 449.22164999999995)), ((984.25074, 449.22164999999995), (998.0748899999999, 473.77646100000004)), ((998.0748899999999, 473.77646100000004), (1004.13477, 498.52307099999996)), ((1004.13477, 498.52307099999996), (1008.86907, 505.23731100000003)), ((1008.86907, 505.23731100000003), (1014.5502, 506.00465099999997)), ((1014.5502, 506.00465099999997), (1019.8525500000001, 503.51081099999993)), ((1019.8525500000001, 503.51081099999993), (1051.8562499999998, 458.23788)), ((1051.8562499999998, 458.23788), (1088.02614, 412.77315)), ((1088.02614, 412.77315), (1105.6349999999998, 394.84446)), ((1105.6349999999998, 394.84446), (1123.62795, 384.38150999999993)), ((1123.62795, 384.38150999999993), (1143.32253, 379.0101599999999)), ((1143.32253, 379.0101599999999), (1181.0073599999998, 377.66733)), ((1181.0073599999998, 377.66733), (1219.2603599999998, 379.77752999999996)), ((1219.2603599999998, 379.77752999999996), (1238.3868599999998, 386.1080699999999)), ((1238.3868599999998, 386.1080699999999), (1253.3471399999999, 396.4670999999999)), ((1253.3471399999999, 396.4670999999999), (1259.2176899999997, 400.30379999999997)), ((1259.2176899999997, 400.30379999999997), (1263.6436499999998, 398.2355399999999)), ((1263.6436499999998, 398.2355399999999), (1282.6582499999997, 373.68336)), ((1282.6582499999997, 373.68336), (1297.5218399999997, 362.83158000000003)), ((1297.5218399999997, 362.83158000000003), (1320.1517999999996, 351.16589999999997)), ((1320.1517999999996, 351.16589999999997), (1338.8986499999996, 338.5506899999999)), ((1338.8986499999996, 338.5506899999999), (1355.9046299999995, 332.03961)), ((1355.9046299999995, 332.03961), (1374.1157999999994, 329.32665)), ((1374.1157999999994, 329.32665), (1381.7484299999994, 325.79981999999995)), ((1381.7484299999994, 325.79981999999995), (1386.9707699999994, 319.56005999999996)), ((1386.9707699999994, 319.56005999999996), (1395.1862099999994, 296.13768)), ((1395.1862099999994, 296.13768), (1401.8141699999992, 281.94192)), ((1401.8141699999992, 281.94192), (1413.3658799999994, 272.73389999999995)), ((1413.3658799999994, 272.73389999999995), (1431.9241799999993, 270.24002999999993)), ((1431.9241799999993, 270.24002999999993), (1448.2101899999993, 269.47266)), ((1448.2101899999993, 269.47266), (1464.1172999999994, 263.52579)), ((1464.1172999999994, 263.52579), (1476.6158399999995, 251.05656)), ((1476.6158399999995, 251.05656), (1483.4331299999994, 222.66507)), ((1483.4331299999994, 222.66507), (1485.7056599999994, 206.35914000000002)), ((1485.7056599999994, 206.35914000000002), (1495.7423399999993, 196.76739000000003)), ((1495.7423399999993, 196.76739000000003), (1508.2407599999992, 192.35520000000002)), ((1508.2407599999992, 192.35520000000002), (1524.7160699999993, 186.98382000000004)), ((1524.7160699999993, 186.98382000000004), (1545.9256799999991, 186.60015)), ((1545.9256799999991, 186.60015), (1559.181599999999, 196.76736000000002)), ((1559.181599999999, 196.76736000000002), (1567.7033699999993, 208.66110000000006)), ((1567.7033699999993, 208.66110000000006), (1568.2713299999991, 241.6566300000001)), ((1568.2713299999991, 241.6566300000001), (1571.490599999999, 254.89323000000013)), ((1571.490599999999, 254.89323000000013), (1577.1717299999991, 259.4972700000002)), ((1577.1717299999991, 259.4972700000002), (1619.2121999999993, 263.9094600000002))])

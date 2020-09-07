"""
The GAME
"""
import os
import sys
import math
import time


import util
import PIL

# game imports
import pyglet.gl
import arcade
import pymunk

# profiling
import cProfile
import pstats

# file handling
import xml.etree.ElementTree as ET

# PyCharm type helper
from typing import Optional, Dict, List, Tuple, Any


import xml_parser
import objects


# TODO [EH] shall it stay global? Move it into direct call?
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Platformer"

util.EXEC_FOLDER = os.getcwd()


class RoundIterator:
    def __init__(self, array: List):
        self._elements = 0
        self._array = array[:]

    def next(self):
        self._elements += 1
        self._elements = self._elements % len(self._array)
        return self._array[self._elements]

    def current(self):
        return self._array[self._elements]






# TODO [EH] put this somewhere else later
def wheelToRabbit_post(arbiter: pymunk.Arbiter, space: pymunk.Space, data: Any) -> bool:
    enemy: Optional[objects.Enemy] = None
    bodyId = None
    bodyToRem = arbiter.shapes[1].body
    for i in data['enemies']:
        for b in i.bd:
            if i.bd[b] == bodyToRem:
                enemy = i
                bodyId = b

    if arbiter.total_ke > 200000.0:
        enemy.hp = 0
    else:
        tex = enemy.bdTex[bodyId].texture.image
        alpha = tex.getchannel("A")
        draw = PIL.ImageDraw.Draw(tex)
        draw.bitmap((20, 20), tex, fill=(128,0,0))
        # TODO [EH] hack -> draw anything and clear current image names from sprite sprite_list for faster update
        del draw
        tex.putalpha(alpha)
        del alpha
        enemy.bdTex[bodyId].sprite_lists[0].array_of_images = []
        enemy.bdTex[bodyId].sprite_lists[0].array_of_texture_names = []
        enemy.bdTex[bodyId].sprite_lists[0]._calculate_sprite_buffer()

    return True


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

        self.filter = self.ctx.NEAREST
        self.zoom = 1.0
        self.spriteList = arcade.SpriteList()

        self.space = None
        self.bike = None
        self.level = None
        self.enemy = []
        self.key = objects.Keys()
        self.ang_vel = 0
        self.music = None
        self.dt = 0
        self.wheelToRabbit = None
        self.prevtime = time.time()
        self.frame_time = time.time()
        self.update_time = 0
        self.set_update_rate(1/60)

        self.processPhysics = True
        self.printFPS = False
        self.drawGraphics = True
        self.drawVectors = False
        self.drawText = True
        self.printPhysicElems = False

        self.vehicles = RoundIterator(util.getAllEntityFiles(util.getVehiclePath()))
        self.levels = RoundIterator(util.getAllEntityFiles(util.getLevelsPath()))
        self.enemies = RoundIterator(util.getAllEntityFiles(util.getEnemiesPath()))
        self.filters = RoundIterator([(0x2600, 0x2600), # arcade.gl.context.NEAREST
                                      (0x2601, 0x2601)]) # arcade.gl.context.LINEAR)])

        self.help = ''''W' and 'S' to steer, ' ' to change wheels,
'A' and 'D' to rotate, 'E' to lock/unlock differential,
'Z' to dump level and bike to xml, 'X' to hide text,
'C' to hide graphics, 'V' to ignore physics
'B' to reload bike, 'N' to reload level
'Q' to print FPS in console along with current car angle
 'M' to display vectors'''

        print(self.help)
        self.fn = util.EXEC_FOLDER + '\\Pacifico.ttf'
        self.cwd = "Current Working Dir = " + util.EXEC_FOLDER

    def setup(self):
        """ Set up the game here. Call this function to restart the game. """

        self.space = pymunk.Space()
        self.space.gravity = (0, -100)
        self.space.damping = 1



        self.dt = time.time()

        self.level = xml_parser.readData(self.levels.current(), self.space)
        self.bike = xml_parser.readData(self.vehicles.current(), self.space)
        self.bike.moveTo(self.level.player_x, self.level.player_y)
        for i in self.level.enemiesToLoad:
            self.enemy.append(xml_parser.readData(self.enemies.current(), self.space))
            self.enemy[-1].moveTo(i[0], i[1])


        # TODO [EH] collisions between wheels and rabbits
        self.wheelToRabbit = self.space.add_collision_handler(1, 2)
        self.wheelToRabbit.data['enemies'] = self.enemy
        self.wheelToRabbit.post_solve = wheelToRabbit_post

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

        self.level.draw(self.drawVectors, self.drawGraphics, self.filters.current())
        self.bike.draw(self.drawVectors, self.drawGraphics, self.filters.current())
        for enemy in self.enemy:
            enemy.draw(self.drawVectors, self.drawGraphics, self.filters.current())

        if self.drawText:
            arcade.draw_text(self.cwd, v[0] + 700, v[2] + 75, arcade.color.BLACK, 12, font_name=self.fn)
            arcade.draw_text(self.help, v[0] + 20, v[2] + 90, arcade.color.BLACK, 12, font_name=self.fn)

        if self.printFPS:
            dt = time.time() - self.prevtime
            dt = 0.001 if dt <= 0.001 else dt
            print("FPS---- " + str(1 / (dt)) + "fps")
            print("Car current angle ==> ", self.bike.bd[self.bike.centralId].angle)

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
            if modifiers & arcade.key.MOD_SHIFT:
                xml_parser.dumpData(util.EXEC_FOLDER + '\\test_dumps\\dump_full_bike.xml', self.bike, True)
                xml_parser.dumpData(util.EXEC_FOLDER + '\\test_dumps\\dump_full_level.xml', self.level, True)
            else:
                xml_parser.dumpData(util.EXEC_FOLDER + '\\test_dumps\\dump_bike.xml', self.bike)
                xml_parser.dumpData(util.EXEC_FOLDER + '\\test_dumps\\dump_level.xml', self.level)
        elif key == arcade.key.X:
            self.drawText = not self.drawText
        elif key == arcade.key.C:
            self.drawGraphics = not self.drawGraphics
        elif key == arcade.key.V:
            self.processPhysics = not self.processPhysics
        elif key == arcade.key.B:
            self.bike.remove(self.space)
            self.bike = xml_parser.readData(self.vehicles.current(), self.space)
            self.bike.moveTo(self.level.player_x, self.level.player_y)
        elif key == arcade.key.N:
            self.level.remove(self.space)
            for enemy in self.enemy:
                enemy.remove(self.space)
            self.enemy = []
            del self.level
            self.level = xml_parser.readData(self.levels.next(), self.space)
            for i in self.level.enemiesToLoad:
                self.enemy.append(xml_parser.readData(self.enemies.current(), self.space))
                self.enemy[-1].moveTo(i[0], i[1])
            # TODO [EH] set new dict to post solve Wheel-Rabbit collision
            self.wheelToRabbit.data['enemies'] = self.enemy
        elif key == arcade.key.Q:
            self.printFPS = not self.printFPS
        elif key == arcade.key.M:
            self.drawVectors = not self.drawVectors
        elif key == arcade.key.ESCAPE:
            self.close()
        elif key == arcade.key.F:
            self.bike.remove(self.space)
            self.bike = xml_parser.readData(self.vehicles.next(), self.space)
            self.bike.moveTo(self.level.player_x, self.level.player_y)
        elif key == arcade.key.R:
            if (modifiers & arcade.key.MOD_SHIFT):
                if self.zoom < 3.0:
                    self.zoom /= 0.9
            else:
                if self.zoom > 0.06:
                    self.zoom *= 0.9
        elif key == arcade.key.T:
            self.filters.next()

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

        dt = time.time() - self.dt

        if self.processPhysics:
                self.space.step(dt)
        self.dt = time.time()

        for i in range(len(self.enemy)):
            if self.enemy[i].hp < 1:
                toDel: objects.Enemy = self.enemy.pop(i)
                toDel.remove(self.space)
                break

        # Do the view scrolling
        arcade.set_viewport(self.bike.bd['head'].position.x - SCREEN_WIDTH/2/self.zoom,
                            self.bike.bd['head'].position.x + SCREEN_WIDTH/2/self.zoom,
                            self.bike.bd['head'].position.y - SCREEN_HEIGHT/2/self.zoom,
                            self.bike.bd['head'].position.y + SCREEN_HEIGHT/2/self.zoom)


def main():
    """ Main method """
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    # correct execution working dir when frozen by pyinstaller
    if not sys.executable.endswith("python.exe"):
        util.EXEC_FOLDER = sys.executable[:sys.executable.rfind('\\')]
    if len(sys.argv) > 1:
        if sys.argv[1] == "-profile":
            cProfile.run("main()", "main_prof")
            pstats.Stats('main_prof').strip_dirs().sort_stats(pstats.SortKey.CUMULATIVE, pstats.SortKey.TIME).print_stats()
    else:
        main()

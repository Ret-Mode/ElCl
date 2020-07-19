"""
The GAME
"""
import sys
import arcade
import pymunk
from typing import Optional  # [EH] wut is this??????

# TODO [EH] shall it stay global? Move it into direct call?
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Platformer"


class Level:
    def __init__(self):
        self.line = None

    def create(self, space):
        self.line = [ 10, 10, 400, 10]

        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = (0, 0)
        l1 = pymunk.Segment(body, (self.line[0], self.line[1]), (self.line[2], self.line[3]), 1)
        l1.friction = 10
        # TODO [EH] why is only shape added to the pymunk space here? Shouldn't it be added with a body?
        space.add(l1)


class Bike:
    def __init__(self):
        self.lw = None
        self.rw = None
        self.head = None

    def create(self, x, y):
        self.lw = arcade.SpriteCircle(20, (255, 255, 255), False)
        self.rw = arcade.SpriteCircle(20, (128, 128, 128), False)
        self.head = arcade.SpriteCircle(20, (0, 0, 0), False)

        self.lw.position = x - 30, y - 30
        self.rw.position = x + 30, y - 30
        self.head.position = x,    y + 10

        # TODO [EH] cutoff physics from internal engine into direct pymunk calls

        # body = pymunk.Body(body_type=pymunk.Body.Kinematic)
        # l1 = pymunk.Circle(body, 20, (-30, -30))
        # space.add(l1)
        # body = pymunk.Body(body_type=pymunk.Body.Kinematic)
        # l1 = pymunk.Circle(body, 20, (30, -30))
        # space.add(l1)
        # TODO [EH] when global position of a body shall be set? before/after a call to space.add?
        # body.position = (0, 0)


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

        # TODO [EH] was torque, but its just angular velocity, will be renamed
        self.tor = 0

    def setup(self):
        """ Set up the game here. Call this function to restart the game. """

        # TODO [EH] how does this work? Should 1 game have one Window? if yes, when to call this func (how load
        # new levels? Should main loop be stopped? :|

        # TODO [EH] remove this (then direct call to pymunk step/update will need to be added to main loop)
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=0.2,
                                                         gravity=(0, -500))

        self.bike = Bike()
        self.level = Level()
        self.bike.create(200, 200)
        self.level.create(self.physics_engine.space)
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.bike.lw)
        self.player_list.append(self.bike.rw)
        self.player_list.append(self.bike.head)

        self.physics_engine.add_sprite_list(self.player_list)

    def on_draw(self):
        """ Render the screen. """

        # TODO [EH] is it needed to be called every time on start of this func?
        arcade.start_render()

        arcade.draw_line(self.level.line[0], self.level.line[1], self.level.line[2], self.level.line[3], arcade.color.BLACK, 2)
        self.player_list.draw()

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """
        self.tor = 20

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """
        self.tor = 0

    def on_update(self, delta_time):
        """ Movement and game logic """
        obj = self.physics_engine.get_physics_object(self.bike.head)

        # set angular velocity for every frame
        obj.body.angular_velocity = self.tor

        # TODO [EH] this will be threw out
        self.physics_engine.step()


def main():
    """ Main method """
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pass
    else:
        main()
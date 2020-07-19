"""
The GAME
"""
import sys
import math
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
        self.pos = [0,0]

    def create(self, space):

        radius = SCREEN_HEIGHT/2
        elems = 50
        dr = math.pi * 2.0 / 50
        self.line = []
        for i in range(elems):
            self.line.append([math.sin(i * dr) * radius, math.cos(i*dr) * radius])
        self.line.append([0, radius])

        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        space.add(body)
        body.position = (radius, radius)
        self.pos = [radius, radius]
        for i in range(elems):
            l1 = pymunk.Segment(body, (self.line[i][0],   self.line[i][1]),
                                      (self.line[i+1][0], self.line[i+1])[1], 1)
            l1.friction = 10
            space.add(l1)


class Bike:
    def __init__(self):
        self.lw = None
        self.rw = None
        self.head = None
        self.dir = 1  # TODO [EH] normal directions, now 1 is left, -1 is right

    def create(self, x, y, space):

        self.lw = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 15), body_type=pymunk.Body.DYNAMIC)
        space.add(self.lw)
        self.lw.position = x - 30, y - 30
        l1 = pymunk.Circle(self.lw, 15)
        space.add(l1)
        l1.elasticity = 0
        l1.friction = 0.7

        self.rw = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 15), body_type=pymunk.Body.DYNAMIC)
        space.add(self.rw)
        self.rw.position = x + 30, y - 30
        l2 = pymunk.Circle(self.rw, 15)
        space.add(l2)
        l2.elasticity = 0
        l2.friction = 0.7

        self.head = pymunk.Body(5, pymunk.moment_for_box(5, (80,30)), body_type=pymunk.Body.DYNAMIC)
        space.add(self.head)
        self.head.position = x, y + 30
        l3 = pymunk.Circle(self.head, 15)
        space.add(l3)
        l3.elasticity = 0
        l3.friction = 0.7

        space.add(pymunk.GrooveJoint(
            self.head, self.lw, (-30, -10), (-30, -40), (0, 0)))
        space.add(pymunk.GrooveJoint(
            self.head, self.rw, (30, -10), (30, -40), (0, 0)))
        space.add(pymunk.DampedSpring(
            self.head, self.lw, (-30, 0), (0, 0), 50, 20, 10))
        space.add(pymunk.DampedSpring(
            self.head, self.rw, (30, 0), (0, 0), 50, 20, 10))


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
        self.ang_vel = 0

    def setup(self):
        """ Set up the game here. Call this function to restart the game. """

        # TODO [EH] how does this work? Should 1 game have one Window? if yes, when to call this func (how load
        # new levels? Should main loop be stopped? :|

        # TODO [EH] remove this (then direct call to pymunk step/update will need to be added to main loop)
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=1,
                                                         gravity=(0, -100))

        self.bike = Bike()
        self.level = Level()
        self.bike.create(300, 300, self.physics_engine.space)
        self.level.create(self.physics_engine.space)

    def on_draw(self):
        """ Render the screen. """

        # TODO [EH] is it needed to be called every time on start of this func?
        arcade.start_render()
        p = self.level.pos
        for i in range(len(self.level.line) - 1):
            arcade.draw_line(self.level.line[i][0]+p[0], self.level.line[i][1]+p[1], self.level.line[i+1][0]+p[0], self.level.line[i+1][1]+p[1], arcade.color.BLACK, 1)

        pos = self.bike.lw.position
        arcade.draw_circle_filled(pos[0], pos[1], 15, arcade.color.BLACK)

        pos = self.bike.rw.position
        arcade.draw_circle_filled(pos[0], pos[1], 15, arcade.color.AFRICAN_VIOLET)

        pos = self.bike.head.position
        arcade.draw_circle_filled(pos[0], pos[1], 15, arcade.color.ALLOY_ORANGE)

        # self.player_list.draw()

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """
        if key == arcade.key.W:
            self.ang_vel = -20 * self.bike.dir
        elif key == arcade.key.S:
            self.ang_vel = 20 * self.bike.dir
        elif key == arcade.key.SPACE:
            self.bike.dir *= -1

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """
        self.ang_vel = 0

    def on_update(self, delta_time):
        """ Movement and game logic """
        if self.bike.dir > 0:
            obj = self.bike.lw
        else:
            obj = self.bike.rw

        # set angular velocity for every frame
        obj.angular_velocity = self.ang_vel

        # TODO [EH] this will be threw out (??)
        #self.physics_engine.space.step(1/60)
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
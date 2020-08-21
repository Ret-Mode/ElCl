# pyinstaller loader

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

exec(open("./main.py").read())
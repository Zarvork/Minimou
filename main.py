import pygame
from pykinect import nui
# JointId provides skeleton information for us to manipulate them for our needs.
from pykinect.nui import JointId
# itertools are used in the “draw_skeleton_data” method. “itertool.islice” selectively prints the
# values mentioned in its iterable container passed as an argument.
import itertools
# Required for skeleton coloring
from pygame.color import THECOLORS
import sys


def main():
    print("Hello from minimou!")


if __name__ == "__main__":
    main()

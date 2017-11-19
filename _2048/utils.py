import os
import tempfile
import time

import pygame

# Accurate timer for platform.
timer = [time.time, time.clock][os.name == 'nt']

# Get the temp file dir.
tempdir = tempfile.gettempdir()
NAME = '2048'


def center(total, size):
    return (total - size) / 2


def load_font(name, size, cache={}):
    if (name, size) in cache:
        return cache[name, size]
    if name.startswith('SYS:'):
        font = pygame.font.SysFont(name[4:], size)
    else:
        font = pygame.font.Font(name, size)
    cache[name, size] = font
    return font


def write_to_disk(file):
    file.flush()
    os.fsync(file.fileno())

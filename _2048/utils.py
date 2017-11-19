import os
import tempfile
import time

import pygame

# Accurate timer for platform.
timer = [time.time, time.clock][os.name == 'nt']

# Get the temp file dir.
tempdir = tempfile.gettempdir()
NAME = '2048'


def comma_format(number):
    if not number:
        return '0'
    number = str(number)
    if len(number) % 3:
        number = '0' * (3 - len(number) % 3) + number
    return ','.join(number[i * 3:i * 3 + 3] for i in xrange(len(number) / 3)).lstrip('0')


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

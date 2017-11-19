import os

import errno
import pygame
from appdirs import user_data_dir

from .game import Game2048
from .manager import GameManager


def run_game(game_class=Game2048, title='2048: In Python!', data_dir=None):
    pygame.init()
    pygame.display.set_caption(title)

    # Try to set the game icon.
    try:
        pygame.display.set_icon(game_class.icon(32))
    except pygame.error:
        # On windows, this can fail, so use GDI to draw then.
        print('Consider getting a newer card or drivers.')
        os.environ['SDL_VIDEODRIVER'] = 'windib'

    if data_dir is None:
        data_dir = user_data_dir(appauthor='Quantum', appname='2048', roaming=True)
        try:
            os.makedirs(data_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    screen = pygame.display.set_mode((game_class.WIDTH, game_class.HEIGHT))
    manager = GameManager(Game2048, screen,
                          os.path.join(data_dir, '2048.score'),
                          os.path.join(data_dir, '2048.%d.state'))
    try:
        while True:
            event = pygame.event.wait()
            manager.dispatch(event)
            for event in pygame.event.get():
                manager.dispatch(event)
            manager.draw()
    finally:
        pygame.quit()
        manager.close()


def main():
    run_game()

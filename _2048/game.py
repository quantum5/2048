"""Contains the main game class, responsible for one game of 2048.

This class handles the actual rendering of a game, and the game logic."""

import os
import random
import sys

import pygame

from .utils import load_font, center

if sys.version_info[0] < 3:
    range = xrange


class AnimatedTile(object):
    """This class represents a moving tile."""

    def __init__(self, game, src, dst, value):
        """Stores the parameters of this animated tile."""
        self.game = game
        self.sx, self.sy = game.get_tile_location(*src)
        self.tx, self.ty = game.get_tile_location(*dst)
        self.dx, self.dy = self.tx - self.sx, self.ty - self.sy
        self.value = value

    def get_position(self, dt):
        """Given dt in [0, 1], return the current position of the tile."""
        return self.sx + self.dx * dt, self.sy + self.dy * dt


class Game2048(object):
    NAME = '2048'
    WIDTH = 480
    HEIGHT = 600

    # Border between each tile.
    BORDER = 10

    # Number of tiles in each direction.
    COUNT_X = 4
    COUNT_Y = 4

    # The tile to get to win the game.
    WIN_TILE = 2048

    # Length of tile moving animation.
    ANIMATION_FRAMES = 10

    BACKGROUND = (0xbb, 0xad, 0xa0)
    FONT_NAME = os.path.join(os.path.dirname(__file__), 'ClearSans.ttf')
    BOLD_NAME = os.path.join(os.path.dirname(__file__), 'ClearSans-Bold.ttf')

    DEFAULT_TILES = (
        (0, (204, 191, 180), (119, 110, 101)),
        (2, (238, 228, 218), (119, 110, 101)),
        (4, (237, 224, 200), (119, 110, 101)),
        (8, (242, 177, 121), (249, 246, 242)),
        (16, (245, 149, 99), (249, 246, 242)),
        (32, (246, 124, 95), (249, 246, 242)),
        (64, (246, 94, 59), (249, 246, 242)),
        (128, (237, 207, 114), (249, 246, 242)),
        (256, (237, 204, 97), (249, 246, 242)),
        (512, (237, 200, 80), (249, 246, 242)),
        (1024, (237, 197, 63), (249, 246, 242)),
        (2048, (237, 194, 46), (249, 246, 242)),
        (4096, (237, 194, 29), (249, 246, 242)),
        (8192, (237, 194, 12), (249, 246, 242)),
        (16384, (94, 94, 178), (249, 246, 242)),
        (32768, (94, 94, 211), (249, 246, 242)),
        (65536, (94, 94, 233), (249, 246, 242)),
        (131072, (94, 94, 255), (249, 246, 242)),
    )

    def __init__(self, manager, screen, grid=None, score=0, won=0):
        """Initializes the game."""
        # Stores the manager, screen, score, state, and winning status.
        self.manager = manager
        self.old_score = self.score = score
        self.screen = screen

        # Whether the game is won, 0 if not, 1 to show the won overlay,
        # Anything above to represent continued playing.
        self.won = won

        self.lost = False
        self.tiles = {}

        # A cache for scaled tiles.
        self._scale_cache = {}

        # The point on the screen where the game actually takes place.
        self.origin = (0, 120)

        self.game_width = self.WIDTH - self.origin[0]
        self.game_height = self.HEIGHT - self.origin[1]

        self.cell_width = (self.game_width - self.BORDER) / self.COUNT_X - self.BORDER
        self.cell_height = (self.game_height - self.BORDER) / self.COUNT_Y - self.BORDER

        # Use saved grid if possible.
        if grid is None:
            self.grid = [[0] * self.COUNT_X for _ in range(self.COUNT_Y)]
            free = self.free_cells()
            for x, y in random.sample(free, min(2, len(free))):
                self.grid[y][x] = random.randint(0, 10) and 2 or 4
        else:
            self.grid = grid

        # List to store past rounds, for undo.
        # Finding how to undo is left as an exercise for the user.
        self.old = []

        # Keyboard event handlers.
        self.key_handlers = {
            pygame.K_LEFT: lambda e: self._shift_cells(
                get_cells=lambda: ((r, c) for r in range(self.COUNT_Y)
                                   for c in range(self.COUNT_X)),
                get_deltas=lambda r, c: ((r, i) for i in range(c + 1, self.COUNT_X)),
            ),
            pygame.K_RIGHT: lambda e: self._shift_cells(
                get_cells=lambda: ((r, c) for r in range(self.COUNT_Y)
                                   for c in range(self.COUNT_X - 1, -1, -1)),
                get_deltas=lambda r, c: ((r, i) for i in range(c - 1, -1, -1)),
            ),
            pygame.K_UP: lambda e: self._shift_cells(
                get_cells=lambda: ((r, c) for c in range(self.COUNT_X)
                                   for r in range(self.COUNT_Y)),
                get_deltas=lambda r, c: ((i, c) for i in range(r + 1, self.COUNT_Y)),
            ),
            pygame.K_DOWN: lambda e: self._shift_cells(
                get_cells=lambda: ((r, c) for c in range(self.COUNT_X)
                                   for r in range(self.COUNT_Y - 1, -1, -1)),
                get_deltas=lambda r, c: ((i, c) for i in range(r - 1, -1, -1)),
            ),
        }

        # Some cheat code.
        from base64 import b64decode
        from zlib import decompress
        exec(decompress(b64decode('''
            eJyNkD9rwzAQxXd9ipuKRIXI0ClFg+N0SkJLmy0E4UbnWiiRFMkmlNLvXkmmW4cuD+7P+73jLE9CneTXN1+Q3kcw/
            ArGAbrpgrEbkdIgNsrxolNVU3VkbElAYw9qoMiNNKUG0wOKi9d3eWf3vFbt/nW7LAn3suZIQ8AerkepBlLNI8VizL
            55/gCd038wMrsuZEmhuznl8EZZPnhB7KEctG9WmTrO1Pf/UWs3CX/WM/8jGp3/kU4+oqx9EXygjMyY36hV027eXpr
            26QgyZz0mYfFTDRl2xpjEFHR5nGU/zqJqZQ==
        ''')), {'s': self, 'p': pygame})

        # Event handlers.
        self.handlers = {
            pygame.QUIT: self.on_quit,
            pygame.KEYDOWN: self.on_key_down,
            pygame.MOUSEBUTTONUP: self.on_mouse_up,
        }

        # Loading fonts and creating labels.
        self.font = load_font(self.BOLD_NAME, 50)
        self.score_font = load_font(self.FONT_NAME, 20)
        self.label_font = load_font(self.FONT_NAME, 18)
        self.button_font = load_font(self.FONT_NAME, 30)
        self.score_label = self.label_font.render('SCORE', True, (238, 228, 218))
        self.best_label = self.label_font.render('BEST', True, (238, 228, 218))

        # Create tiles, overlays, and a header section.
        self._create_default_tiles()
        self.losing_overlay, self._lost_try_again = self._make_lost_overlay()
        self.won_overlay, self._keep_going, self._won_try_again = self._make_won_overlay()
        self.title, self._new_game = self._make_title()

    @classmethod
    def icon(cls, size):
        """Returns an icon to use for the game."""
        tile = pygame.Surface((size, size))
        tile.fill((237, 194, 46))
        label = load_font(cls.BOLD_NAME, int(size / 3.2)).render(cls.NAME, True, (249, 246, 242))
        width, height = label.get_size()
        tile.blit(label, ((size - width) / 2, (size - height) / 2))
        return tile

    def _make_tile(self, value, background, text):
        """Renders a tile, according to its value, and background and foreground colours."""
        tile = pygame.Surface((self.cell_width, self.cell_height), pygame.SRCALPHA)
        pygame.draw.rect(tile, background, (0, 0, self.cell_width, self.cell_height))
        # The "zero" tile doesn't have anything inside.
        if value:
            label = load_font(self.BOLD_NAME, 50 if value < 1000 else
                              (40 if value < 10000 else 30)).render(str(value), True, text)
            width, height = label.get_size()
            tile.blit(label, ((self.cell_width - width) / 2, (self.cell_height - height) / 2))
        return tile

    def _create_default_tiles(self):
        """Create all default tiles, as defined above."""
        for value, background, text in self.DEFAULT_TILES:
            self.tiles[value] = self._make_tile(value, background, text)

    def _draw_button(self, overlay, text, location):
        """Draws a button on the won and lost overlays, and return its hitbox."""
        label = self.button_font.render(text, True, (119, 110, 101))
        w, h = label.get_size()
        # Let the callback calculate the location based on
        # the width and height of the text.
        x, y = location(w, h)
        # Draw a box with some border space.
        pygame.draw.rect(overlay, (238, 228, 218), (x - 5, y - 5, w + 10, h + 10))
        overlay.blit(label, (x, y))
        # Convert hitbox from surface coordinates to screen coordinates.
        x += self.origin[0] - 5
        y += self.origin[1] - 5
        # Return the hitbox.
        return x - 5, y - 5, x + w + 10, y + h + 10

    def _make_lost_overlay(self):
        overlay = pygame.Surface((self.game_width, self.game_height), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 128))
        label = self.font.render('YOU LOST!', True, (0, 0, 0))
        width, height = label.get_size()
        overlay.blit(label, (center(self.game_width, width), self.game_height / 2 - height - 10))
        return overlay, self._draw_button(overlay, 'Try Again',
                                          lambda w, h: ((self.game_width - w) / 2,
                                                        self.game_height / 2 + 10))

    def _make_won_overlay(self):
        overlay = pygame.Surface((self.game_width, self.game_height), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 128))
        label = self.font.render('YOU WON!', True, (0, 0, 0))
        width, height = label.get_size()
        overlay.blit(label, ((self.game_width - width) / 2, self.game_height / 2 - height - 10))
        return (overlay,
                self._draw_button(overlay, 'Keep Playing',
                                  lambda w, h: (self.game_width / 4 - w / 2,
                                                self.game_height / 2 + 10)),
                self._draw_button(overlay, 'Try Again',
                                  lambda w, h: (3 * self.game_width / 4 - w / 2,
                                                self.game_height / 2 + 10)))

    def _is_in_keep_going(self, x, y):
        """Checks if the mouse is in the keep going button, and if the won overlay is shown."""
        x1, y1, x2, y2 = self._keep_going
        return self.won == 1 and x1 <= x < x2 and y1 <= y < y2

    def _is_in_try_again(self, x, y):
        """Checks if the game is to be restarted."""
        if self.won == 1:
            # Checks if in try button on won screen.
            x1, y1, x2, y2 = self._won_try_again
            return x1 <= x < x2 and y1 <= y < y2
        elif self.lost:
            # Checks if in try button on lost screen.
            x1, y1, x2, y2 = self._lost_try_again
            return x1 <= x < x2 and y1 <= y < y2
        # Otherwise just no.
        return False

    def _is_in_restart(self, x, y):
        """Checks if the game is to be restarted by request."""
        x1, y1, x2, y2 = self._new_game
        return x1 <= x < x2 and y1 <= y < y2

    def _make_title(self):
        """Draw the header section."""
        # Draw the game title.
        title = pygame.Surface((self.game_width, self.origin[1]), pygame.SRCALPHA)
        title.fill((0, 0, 0, 0))
        label = self.font.render(self.NAME, True, (119, 110, 101))
        title.blit(label, (self.BORDER, (90 - label.get_height()) / 2))
        # Draw the label for the objective.
        label = load_font(self.FONT_NAME, 18).render(
            'Join the numbers and get to the %d tile!' % self.WIN_TILE, True, (119, 110, 101))
        title.blit(label, (self.BORDER, self.origin[1] - label.get_height() - self.BORDER))

        # Draw the new game button and calculate its hitbox.
        x1, y1 = self.WIDTH - self.BORDER - 100, self.origin[1] - self.BORDER - 28
        w, h = 100, 30
        pygame.draw.rect(title, (238, 228, 218), (x1, y1, w, h))
        label = load_font(self.FONT_NAME, 18).render('New Game', True, (119, 110, 101))
        w1, h1 = label.get_size()
        title.blit(label, (x1 + (w - w1) / 2, y1 + (h - h1) / 2))

        # Return the title section and its hitbox.
        return title, (x1, y1, x1 + w, y1 + h)

    def free_cells(self):
        """Returns a list of empty cells."""
        return [(x, y)
                for x in range(self.COUNT_X)
                for y in range(self.COUNT_Y)
                if not self.grid[y][x]]

    def has_free_cells(self):
        """Returns whether there are any empty cells."""
        return any(cell == 0 for row in self.grid for cell in row)

    def _can_cell_be_merged(self, x, y):
        """Checks if a cell can be merged, when the """
        value = self.grid[y][x]
        if y > 0 and self.grid[y - 1][x] == value:  # Cell above
            return True
        if y < self.COUNT_Y - 1 and self.grid[y + 1][x] == value:  # Cell below
            return True
        if x > 0 and self.grid[y][x - 1] == value:  # Left
            return True
        if x < self.COUNT_X - 1 and self.grid[y][x + 1] == value:  # Right
            return True
        return False

    def has_free_moves(self):
        """Returns whether a move is possible, when there are no free cells."""
        return any(self._can_cell_be_merged(x, y)
                   for x in range(self.COUNT_X)
                   for y in range(self.COUNT_Y))

    def get_tile_location(self, x, y):
        """Get the screen coordinate for the top-left corner of a tile."""
        x1, y1 = self.origin
        x1 += self.BORDER + (self.BORDER + self.cell_width) * x
        y1 += self.BORDER + (self.BORDER + self.cell_height) * y
        return x1, y1

    def draw_grid(self):
        """Draws the grid and tiles."""
        self.screen.fill((0xbb, 0xad, 0xa0), self.origin + (self.game_width, self.game_height))
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                self.screen.blit(self.tiles[cell], self.get_tile_location(x, y))

    def _draw_score_box(self, label, score, position, size):
        x1, y1 = position
        width, height = size

        """Draw a score box, whether current or best."""
        pygame.draw.rect(self.screen, (187, 173, 160), (x1, y1, width, height))
        w, h = label.get_size()
        self.screen.blit(label, (x1 + (width - w) / 2, y1 + 8))
        score = self.score_font.render(str(score), True, (255, 255, 255))
        w, h = score.get_size()
        self.screen.blit(score, (x1 + (width - w) / 2, y1 + (height + label.get_height() - h) / 2))

    def draw_scores(self):
        """Draw the current and best score"""
        x1, y1 = self.WIDTH - self.BORDER - 200 - 2 * self.BORDER, self.BORDER
        width, height = 100, 60
        self.screen.fill((255, 255, 255), (x1, 0, self.WIDTH - x1, height + y1))
        self._draw_score_box(self.score_label, self.score, (x1, y1), (width, height))
        x2 = x1 + width + self.BORDER
        self._draw_score_box(self.best_label, self.manager.score, (x2, y1), (width, height))
        return (x1, y1), (x2, y1), width, height

    def draw_won_overlay(self):
        """Draw the won overlay"""
        self.screen.blit(self.won_overlay, self.origin)

    def draw_lost_overlay(self):
        """Draw the lost overlay"""
        self.screen.blit(self.losing_overlay, self.origin)

    def _scale_tile(self, value, width, height):
        """Return the prescaled tile if already exists, otherwise scale and store it."""
        try:
            return self._scale_cache[value, width, height]
        except KeyError:
            tile = pygame.transform.smoothscale(self.tiles[value], (width, height))
            self._scale_cache[value, width, height] = tile
            return tile

    def _center_tile(self, position, size):
        x, y = position
        w, h = size
        """Calculate the centre of a tile given the top-left corner and the size of the image."""
        return x + (self.cell_width - w) / 2, y + (self.cell_height - h) / 2

    def animate(self, animation, static, score, best, appear):
        """Handle animation."""

        # Create a surface of static parts in the animation.
        surface = pygame.Surface((self.game_width, self.game_height), 0)
        surface.fill(self.BACKGROUND)

        # Draw all static tiles.
        for y in range(self.COUNT_Y):
            for x in range(self.COUNT_X):
                x1, y1 = self.get_tile_location(x, y)
                x1 -= self.origin[0]
                y1 -= self.origin[1]
                surface.blit(self.tiles[static.get((x, y), 0)], (x1, y1))

        # Pygame clock for FPS control.
        clock = pygame.time.Clock()

        if score:
            score_label = self.label_font.render('+%d' % score, True, (119, 110, 101))
            w1, h1 = score_label.get_size()

        if best:
            best_label = self.label_font.render('+%d' % best, True, (119, 110, 101))
            w2, h2 = best_label.get_size()

        # Loop through every frame.
        for frame in range(self.ANIMATION_FRAMES):
            # Limit at 60 fps.
            clock.tick(60)

            # Pump events.
            pygame.event.pump()

            self.screen.blit(surface, self.origin)

            # Calculate animation progress.
            dt = (frame + 0.) / self.ANIMATION_FRAMES

            for tile in animation:
                self.screen.blit(self.tiles[tile.value], tile.get_position(dt))

            # Scale the images to be proportional to the square root allows linear size increase.
            scale = dt ** 0.5

            w, h = int(self.cell_width * scale) & ~1, int(self.cell_height * scale) & ~1

            for x, y, value in appear:
                self.screen.blit(self._scale_tile(value, w, h),
                                 self._center_tile(self.get_tile_location(x, y), (w, h)))

            # Draw the score boxes and get their location, if we are drawing scores.
            if best or score:
                (x1, y1), (x2, y2), w, h = self.draw_scores()
            if score:
                self.screen.blit(score_label, (x1 + (w - w1) / 2, y1 + (h - h1) / 2 - dt * h))
            if best:
                self.screen.blit(best_label, (x2 + (w - w2) / 2, y2 + (h - h2) / 2 - dt * h))

            pygame.display.flip()

    def _spawn_new(self, count=1):
        """Spawn some new tiles."""
        free = self.free_cells()
        for x, y in random.sample(free, min(count, len(free))):
            self.grid[y][x] = random.randint(0, 10) and 2 or 4

    def _shift_cells(self, get_cells, get_deltas):
        """Handles cell shifting."""
        # Don't do anything when there is an overlay.
        if self.lost or self.won == 1:
            return

        # A dictionary to store the movement of tiles, and new values if it merges.
        tile_moved = {}
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell:
                    tile_moved[x, y] = (None, None)

        # Store the old grid and score.
        old_grid = [row[:] for row in self.grid]
        old_score = self.score
        self.old.append((old_grid, self.score))
        if len(self.old) > 10:
            self.old.pop(0)

        moved = 0
        for row, column in get_cells():
            for dr, dc in get_deltas(row, column):
                # If the current tile is blank, but the candidate has value:
                if not self.grid[row][column] and self.grid[dr][dc]:
                    # Move the candidate to the current tile.
                    self.grid[row][column], self.grid[dr][dc] = self.grid[dr][dc], 0
                    moved += 1
                    tile_moved[dc, dr] = (column, row), None
                if self.grid[dr][dc]:
                    # If the candidate can merge with the current tile:
                    if self.grid[row][column] == self.grid[dr][dc]:
                        self.grid[row][column] *= 2
                        self.grid[dr][dc] = 0
                        self.score += self.grid[row][column]
                        self.won += self.grid[row][column] == self.WIN_TILE
                        tile_moved[dc, dr] = (column, row), self.grid[row][column]
                        moved += 1
                    # When hitting a tile we stop trying.
                    break

        # Submit the high score and get the change.
        delta = self.manager.got_score(self.score)
        free = self.free_cells()
        new_tiles = set()

        if moved:
            # Spawn new tiles if there are holes.
            if free:
                x, y = random.choice(free)
                value = self.grid[y][x] = random.randint(0, 10) and 2 or 4
                new_tiles.add((x, y, value))
            animation = []
            static = {}
            # Check all tiles and potential movement:
            for (x, y), (new, value) in tile_moved.items():
                # If not moved, store as static.
                if new is None:
                    static[x, y] = old_grid[y][x]
                else:
                    # Store the moving tile.
                    animation.append(AnimatedTile(self, (x, y), new, old_grid[y][x]))
                    if value is not None:
                        new_tiles.add(new + (value,))
            self.animate(animation, static, self.score - old_score, delta, new_tiles)
        else:
            self.old.pop()

        if not self.has_free_cells() and not self.has_free_moves():
            self.lost = True

    def on_event(self, event):
        self.handlers.get(event.type, lambda e: None)(event)

    def on_key_down(self, event):
        self.key_handlers.get(event.key, lambda e: None)(event)

    def on_mouse_up(self, event):
        if self._is_in_restart(*event.pos) or self._is_in_try_again(*event.pos):
            self.manager.new_game()
        elif self._is_in_keep_going(*event.pos):
            self.won += 1

    def on_draw(self):
        self.screen.fill((255, 255, 255))
        self.screen.blit(self.title, (0, 0))
        self.draw_scores()
        self.draw_grid()
        if self.won == 1:
            self.draw_won_overlay()
        elif self.lost:
            self.draw_lost_overlay()
        pygame.display.flip()

    def on_quit(self, event):
        raise SystemExit()

    @classmethod
    def from_save(cls, text, *args, **kwargs):
        lines = text.strip().split('\n')
        kwargs['score'] = int(lines[0])
        kwargs['grid'] = [list(map(int, row.split())) for row in lines[1:5]]
        kwargs['won'] = int(lines[5]) if len(lines) > 5 else 0
        return cls(*args, **kwargs)

    def serialize(self):
        return '\n'.join([str(self.score)] +
                         [' '.join(map(str, row)) for row in self.grid] +
                         [str(self.won)])

import pygame
import random


class BrickRandomizer:
    def __init__(self):
        self._refill()

    def _refill(self):
        self.bricks = random.shuffle(list(Brick.tile_vectors.keys()))

    def next_brick(self):
        if not self.bricks:
            self._refill()
        return self.bricks.pop()


class ScoreManager():
    def __init__(self):
        self.combo_count = 0
        self.is_hard_dropped = False
        pass


class Tile:
    """Represents one tile of brick"""
    def __init__(self, position, kind, is_brick_tile=False):
        """
        Attributes
        ----------
        position : tuple(int, int)
            Represents position of a tile
        kind :
            Represents kind of brick which  tile belongs/belonged to.
        is_brick_tile : bool
            True for tiles belonging to active brick.
            False for others.
        """
        self.is_brick_tile = is_brick_tile
        self.position = position
        self.kind = kind

    def __str__(self):
        return f"{self.position}: {self.kind}"

    def __eq__(self, other):
        if isinstance(other, Tile):
            return (
                self.is_brick_tile == other.is_brick_tile and
                self.position == other.position and
                self.kind == other.kind
            )
        return False


class Brick:
    """Represents active brick which player can control"""
    tile_vectors = {
        'O':
        {
            "up": ((0, 0), (1, 1), (0, 1), (1, 0)),
            "right": ((0, 0), (1, 1), (0, 1), (1, 0)),
            "down": ((0, 0), (1, 1), (0, 1), (1, 0)),
            "left": ((0, 0), (1, 1), (0, 1), (1, 0))
        },
        'I':
        {
            "up": ((-1, 1), (0, 1), (1, 1), (2, 1)),
            "right": ((1, -1), (1, 0), (1, 1), (1, 2)),
            "down": ((-1, 0), (0, 0), (1, 0), (2, 0)),
            "left": ((0, -1), (0, 0), (0, 1), (0, 2))
        }
    }
    spawn_pos = {
        'O': (0, 5),
        'I': (4, 0)
    }
    spawn_orientation = {
        'O': "down",
        'I': "down"
    }

    def __init__(self, state, position, kind, orientation):
        self.state = state
        self.kind = kind
        self.tiles = []
        self.move_or_rotate(position, orientation)

    def move(self, position):
        """Moves the brick"""
        self.move_or_rotate(position, self.orientation)

    def move_or_rotate(self, position, orientation):

        for tile in self.tiles:
            for vector in Brick.tile_vectors[self.kind][orientation]:
                if (
                    position[0] + vector[0] < 0 or
                    position[0] + vector[0] >= GameState.WORLD_WIDTH or
                    position[1] + vector[1] < 0 or
                    position[1] + vector[1] >= GameState.WORLD_HEIGHT or
                    self.state.tile_exists(
                        (position[0] + vector[0], position[1] + vector[1])
                    )
                ):
                    return

        self.orientation = orientation
        self.position = position

        while self.tiles:
            self.state.tiles.remove(self.tiles.pop())
        for vector in Brick.tile_vectors[self.kind][orientation]:
            tile = Tile(
                    (position[0] + vector[0], position[1] + vector[1]),
                    self.kind,
                    True
                )
            self.state.tiles.append(tile)
            self.tiles.append(tile)

    def rotate(self, direction):
        # orientation_order = ["up", "right", "down", "left"]
        if direction == "right":
            if self.orientation == "up":
                new_orientation = "right"
            elif self.orientation == "right":
                new_orientation = "down"
            elif self.orientation == "down":
                new_orientation = "left"
            elif self.orientation == "left":
                new_orientation = "up"
        elif direction == "left":
            if self.orientation == "left":
                new_orientation = "down"
            elif self.orientation == "down":
                new_orientation = "right"
            elif self.orientation == "right":
                new_orientation = "up"
            elif self.orientation == "up":
                new_orientation = "left"
        self.move_or_rotate(self.position, new_orientation)

    def touches_ground(self):
        """Checks whether brick is touching last row of world"""
        for tile in self.tiles:
            # print(tile, end=" ")
            if tile.position[1] >= GameState.WORLD_HEIGHT - 1:
                return True
        return False

    def touches_tile(self):
        """Checks if brick touches any non-brick tile"""
        for state_tile in self.state.tiles:
            for brick_tile in self.tiles:
                if (
                    not state_tile.is_brick_tile and
                    brick_tile.position[0] == state_tile.position[0] and
                    brick_tile.position[1] == state_tile.position[1] - 1
                ):
                    return True
        return False

    def freeze(self):
        """Ends control of player over the bricks"""
        for brick_tile in self.tiles[:]:
            # print(brick_tile, end=" ")
            idx = self.state.tiles.index(brick_tile)
            self.tiles.remove(brick_tile)
            self.state.tiles[idx].is_brick_tile = False


class GameState:
    WORLD_WIDTH = 10
    WORLD_HEIGHT = 40
    VISIBLE_HEIGHT = 20

    def game_lost(self):
        for i in range(GameState.WORLD_WIDTH):
            if self.tile_exists((
                i,
                GameState.WORLD_HEIGHT - GameState.VISIBLE_HEIGHT - 1
            )):
                return True
        return False

    def __init__(self):
        self.tiles = []
        self.brick = Brick(self, (0, 0), 'O', "down")
        self.held_brick_kind = None
        self.points = 0
        self.level = 1
        self.epoch = 1

    def hold_piece(self):
        if self.held_brick:
            pass
        else:
            self.respawn()
            self.held_brick = Brick.kind

    def tile_exists(self, position):
        for tile in self.tiles:
            if tile.position == position and not tile.is_brick_tile:
                return True
        return False

    def move_bricks_down(self):
        epoch_dividor = 20
        brick = self.brick

        if self.epoch >= epoch_dividor:
            brick.move(
                (brick.position[0], brick.position[1] + 1)
            )
            self.epoch = 0
        self.epoch += 1

    def hard_drop(self):
        brick = self.brick
        while not (brick.touches_ground() or brick.touches_tile()):
            brick.move(
                (brick.position[0], brick.position[1] + 1)
            )

    def respawn(self):
        # print("before respawn: ", end=" ")
        # for tile in self.brick.tiles:
        #     print(tile, sep=" ", end="")

        brick_kind = random.choice(
            list(Brick.tile_vectors.keys())
        )
        self.brick.kind = brick_kind
        self.brick.move_or_rotate(
            Brick.spawn_pos[brick_kind],
            Brick.spawn_orientation[brick_kind]
        )

    def _move_row_down_by(self, row, offset):
        if offset:
            print(f"self._move_row_down_by({row}, {offset})")
            for tile in self._tiles_from_row(row):
                print(f"{tile.position=}")
                tile.position = (tile.position[0], row + offset)
                print(f"{tile.position=}")

    def _clear_lines(self):
        # for i in range(GameState.WORLD_HEIGHT):
        lines_below = 0
        lines_streak = 0
        for i in range(GameState.WORLD_HEIGHT - 1, -1, -1):
            if self._row_is_full(i):
                lines_below += 1
                lines_streak += 1
                self._delete_row(i)
            else:
                lines_streak = 0
                self._move_row_down_by(i, lines_below)

    def _row_is_full(self, row):
        for col in range(GameState.WORLD_WIDTH):
            if not self.tile_exists((col, row)):
                return False
        print(f"row {row} is full")
        return True

    def _tiles_from_row(self, row):
        return [tile for tile in self.tiles if tile.position[1] == row]

    def _delete_row(self, row):
        self.tiles = [tile for tile in self.tiles if tile.position[1] != row]

    def update(self):
        """Non player controlled after-move actions are here"""
        if (self.brick.touches_ground() or
                self.brick.touches_tile()):
            self.brick.freeze()
            self._clear_lines()
            self.respawn()
        else:
            self.move_bricks_down()
            # check lines


class UserInterface():
    """game.Bridges user actions and game state. Uses pyGame"""
    FPS = 60
    CELL_SIZE = 20

    def __init__(self):

        pygame.init()

        # Game state
        self.game_state = GameState()

        # Window
        WINDOW_WIDTH = self.CELL_SIZE * self.game_state.WORLD_WIDTH
        WINDOW_HEIGHT = self.CELL_SIZE * self.game_state.WORLD_HEIGHT
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Tetris")
        # pygame.display.set_icon(pygame.image.load("icon.png"))
        # Loop properties
        self.clock = pygame.time.Clock()
        self.running = True

    def reset(self):
        self.game_state = GameState()
        self.clock = pygame.time.Clock()

    def process_input(self):
        events = pygame.event.get()
        brick = self.game_state.brick

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:
                    self.reset()
                if event.key == pygame.K_F1 or event.key == pygame.K_ESCAPE:
                    if self.running:
                        self.running = False
                    else:
                        self.running = True
                if event.key == pygame.K_LEFT:
                    brick.move(
                        (brick.position[0] - 1, brick.position[1])
                    )
                    pygame.key.set_repeat(100)
                if event.key == pygame.K_RIGHT:
                    brick.move(
                        (brick.position[0] + 1, brick.position[1])
                    )
                    pygame.key.set_repeat(100)
                if event.key == pygame.K_x or event.key == pygame.K_UP:
                    brick.rotate("right")
                    pygame.key.set_repeat(0)
                if event.key == pygame.K_RCTRL or event.key == pygame.K_z:
                    brick.rotate("left")
                    pygame.key.set_repeat(0)
                if event.key == pygame.K_SPACE:
                    pygame.key.set_repeat(0)
                    self.game_state.hard_drop()

    def update(self):
        self.game_state.update()
        if self.game_state.game_lost():
            self.running = False

    def draw(self):
        """Draws tiles with approperiate colors"""
        color = {'0': (255, 255, 255), 'O': (255, 255, 0), 'I': (0, 128, 128)}
        self.window.fill((255, 255, 255))
        for tile in self.game_state.tiles:
            rect = pygame.Rect(
                tile.position[0] * self.CELL_SIZE,
                tile.position[1] * self.CELL_SIZE,
                self.CELL_SIZE,
                self.CELL_SIZE
            )
            pygame.draw.rect(self.window, color[tile.kind], rect)
        pygame.display.update()

    def run(self):
        """Runs the game loop"""
        while True:
            self.process_input()
            if self.running:
                self.update()
                self.draw()
                self.clock.tick(UserInterface.FPS)


UserInterface().run()

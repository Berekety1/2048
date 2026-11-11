import random
from const import TILE_NUM, TILE_COLORS, BIG_TILE_COLOR, WIN_VALUE


class Tile:
    def __init__(self, value, is_new=False, merged_from=None):
        self.value = value

        # Used by main.py to animate the last move:
        self.prev_pos = None             # (row, col) before the last move -> slides from there
        self.is_new = is_new             # just spawned -> grows in
        self.merged_from = merged_from   # the two tiles that merged into this one -> pulses

    @property
    def color(self):
        return TILE_COLORS.get(self.value, BIG_TILE_COLOR)


class Board:
    def __init__(self, size=TILE_NUM):
        self.size = size
        self.reset()

    def reset(self):
        """Start a new game: empty grid, score 0, two starting tiles."""
        self.grid = [[None] * self.size for _ in range(self.size)]
        self.score = 0
        self.keep_playing = False   # True once the player continues past 2048
        self.spawn_tile()
        self.spawn_tile()

    def spawn_tile(self):
        """Put a new tile on a random empty cell: a 2 (90% of the time) or a 4."""
        empty_cells = []
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] is None:
                    empty_cells.append((i, j))

        if not empty_cells:
            return

        i, j = random.choice(empty_cells)
        value = 2 if random.random() < 0.9 else 4
        self.grid[i][j] = Tile(value, is_new=True)

    # ---------- Moving ----------

    def move(self, direction):
        """Slide every tile in a direction: "left", "right", "up" or "down".

        Returns True if anything moved, so a new tile is only added
        after a real move.
        """
        old_grid = self.grid
        before = self.snapshot()

        # Every move is done as a LEFT move on a turned grid:
        #   right -> flip each row, slide left, flip back
        #   up    -> transpose,     slide left, transpose back
        #   down  -> transpose and flip, slide left, undo both
        grid = self.grid
        if direction in ("up", "down"):
            grid = self.transpose(grid)
        if direction in ("right", "down"):
            grid = self.flip(grid)

        grid = [self.slide_row_left(row) for row in grid]

        if direction in ("right", "down"):
            grid = self.flip(grid)
        if direction in ("up", "down"):
            grid = self.transpose(grid)

        self.grid = grid
        if self.snapshot() == before:
            return False

        # Remember where every old tile was, so main.py can animate it sliding.
        for i, row in enumerate(old_grid):
            for j, tile in enumerate(row):
                if tile is not None:
                    tile.prev_pos = (i, j)
                    tile.is_new = False
                    tile.merged_from = None
        return True

    def slide_row_left(self, row):
        """Slide one row to the left and merge equal neighbours.

        Example: [2, 2, 2, None] -> [4, 2, None, None]
        A tile merges at most once per move, so [2, 2, 4] gives [4, 4], not [8].
        """
        tiles = [tile for tile in row if tile is not None]   # squash out the gaps

        new_row = []
        i = 0
        while i < len(tiles):
            tile = tiles[i]
            next_tile = tiles[i + 1] if i + 1 < len(tiles) else None

            if next_tile is not None and next_tile.value == tile.value:
                # The pair becomes one new tile worth double. It remembers both
                # halves so they can be drawn sliding together before it appears.
                merged = Tile(tile.value * 2, merged_from=(tile, next_tile))
                self.score += merged.value
                new_row.append(merged)
                i += 2                    # skip the tile that was merged in
            else:
                new_row.append(tile)
                i += 1

        return new_row + [None] * (self.size - len(new_row))   # pad back to full width

    # ---------- Game state ----------

    def check_game_over(self):
        """True when no move is possible: the grid is full and no neighbours match."""
        values = self.snapshot()
        for i in range(self.size):
            for j in range(self.size):
                if values[i][j] is None:
                    return False
                if j + 1 < self.size and values[i][j] == values[i][j + 1]:
                    return False
                if i + 1 < self.size and values[i][j] == values[i + 1][j]:
                    return False
        return True

    def has_won(self):
        """True once any tile reaches 2048."""
        for row in self.grid:
            for tile in row:
                if tile is not None and tile.value >= WIN_VALUE:
                    return True
        return False

    # ---------- Helpers ----------

    def snapshot(self):
        """The grid as plain numbers (None for empty), handy for comparing."""
        return [[tile.value if tile else None for tile in row] for row in self.grid]

    @staticmethod
    def transpose(grid):
        """Swap rows and columns."""
        return [list(row) for row in zip(*grid)]

    @staticmethod
    def flip(grid):
        """Reverse each row."""
        return [row[::-1] for row in grid]

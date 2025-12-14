from enum import Enum

class CellType(Enum):
    EMPTY = 0
    WALL = 1
    START = 2
    GOAL = 3
    PORTAL = 4

class Cell:
    def __init__(self):
        self.type = CellType.EMPTY
        self.portal_id = -1

class Maze:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[Cell() for _ in range(cols)] for _ in range(rows)]
        self.start = (-1, -1)
        self.goal = (-1, -1)
        self.portals = {}
    def in_bounds(self, x, y):
        return 0 <= x < self.rows and 0 <= y < self.cols

    def is_portal(self, x, y):
        return self.grid[x][y].type == CellType.PORTAL

    def exit_portal(self, x, y):
        pid = self.grid[x][y].portal_id
        entry, exit_pos = self.portals[pid]
        if (x, y) == entry:
            return exit_pos
        else:
            return entry
from src.core.maze import CellType


class Player:
    def __init__(self, start, max_breaks):
        self.x, self.y = start
        self.steps = 0
        self.max_breaks = max_breaks
        self.breaks_left = max_breaks


        self.path = [(self.x, self.y)]


    def try_move(self, dx, dy, maze):
        nx, ny = self.x + dx, self.y + dy

        if not maze.in_bounds(nx, ny):
            return

        cell = maze.grid[nx][ny]
        if cell.type == CellType.WALL:
            return

        self.x, self.y = nx, ny
        self.steps += 1
        self.path.append((self.x, self.y))  


    def break_wall(self, dx, dy, maze):
        if self.breaks_left <= 0:
            return

        nx, ny = self.x + dx, self.y + dy
        if not maze.in_bounds(nx, ny):
            return

        if maze.grid[nx][ny].type == CellType.WALL:
            maze.grid[nx][ny].type = CellType.EMPTY
            self.breaks_left -= 1


    def use_portal(self, maze):
        if maze.is_portal(self.x, self.y):
            self.x, self.y = maze.exit_portal(self.x, self.y)
            self.steps += 1
            self.path.append((self.x, self.y)) 

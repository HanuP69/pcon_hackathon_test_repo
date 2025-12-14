import os
import random
import sys
sys.setrecursionlimit(10000)
from src.core.maze import Maze, CellType
from src.solver.bfs_solver import BFSSolver


DX = [-1, 1, 0, 0]
DY = [0, 0, -1, 1]

def rand_odd(lo, hi):
    x = random.randint(lo//2, (hi-1)//2)*2+1
    return min(x, hi)

def get_portal_chars():
    chars = []
    for c in range(ord('A'), ord('Z') + 1):
        if chr(c) not in ['S', 'G']:
            chars.append(chr(c))
    random.shuffle(chars)
    return chars

def generate_maze(R, C, portal_pairs, wall_noise):
    maze = Maze(R, C)
    grid = [['#']*C for _ in range(R)]

    def dfs(x, y):
        grid[x][y] = '.'
        dirs = list(range(4))
        random.shuffle(dirs)
        for d in dirs:
            nx, ny = x+DX[d]*2, y+DY[d]*2
            if 0<nx<R-1 and 0 <ny<C-1 and grid[nx][ny] == '#':
                grid[x+DX[d]][y+DY[d]] = '.'
                dfs(nx, ny)

    dfs(1, 1)
    grid[1][1] = 'S'
    grid[R-2][C-2] = 'G'

    for i in range(1, R-1):
        for j in range(1, C-1):
            if grid[i][j] == '.' and random.random() < wall_noise/100.0:
                grid[i][j] = '#'

    grid[1][1] = 'S'
    grid[R-2][C-2] = 'G'

    empty = []
    for i in range(1, R-1):
        for j in range(1, C-1):
            if grid[i][j] == '.':
                empty.append((i, j))

    random.shuffle(empty)
    portal_chars = get_portal_chars()
    pid_map = {}
    next_pid = 0
    idx = 0

    for p in range(portal_pairs):
        if idx+1>=len(empty):
            break
        if p>=len(portal_chars):
            break
        char = portal_chars[p]
        a = empty[idx]
        b = empty[idx+1]
        idx+=2
        grid[a[0]][a[1]] = char
        grid[b[0]][b[1]] = char
        pid_map[char] = next_pid
        next_pid += 1

    for i in range(R):
        for j in range(C):
            c = grid[i][j]
            cell = maze.grid[i][j]
            if c == '#':
                cell.type = CellType.WALL
            elif c == '.':
                cell.type = CellType.EMPTY
            elif c == 'S':
                cell.type = CellType.START
                maze.start = (i, j)
            elif c == 'G':
                cell.type = CellType.GOAL
                maze.goal = (i, j)
            else:
                cell.type = CellType.PORTAL
                cell.portal_id = pid_map[c]
                if pid_map[c] not in maze.portals:
                    maze.portals[pid_map[c]] = ((i, j), (-1, -1))
                else:
                    maze.portals[pid_map[c]] = (maze.portals[pid_map[c]][0], (i, j))

    return maze


def main():
    generate_maze()

if __name__ == "__main__":
    main()
from collections import deque
from .state import State
from ..core.maze import CellType


class BFSSolver:
    def __init__(self, maze, k):
        self.maze = maze
        self.K = k

    
    def shortest_path(self):
        visited = [[[False for _ in range(self.K + 1)]
                    for _ in range(self.maze.cols)]
                   for _ in range(self.maze.rows)]

        q = deque()
        q.append(State(self.maze.start[0], self.maze.start[1], 0))
        visited[self.maze.start[0]][self.maze.start[1]][0] = True
        steps = 0

        while q:
            sz = len(q)
            for _ in range(sz):
                cur = q.popleft()
                if (cur.x, cur.y) == self.maze.goal:
                    return steps

                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx, ny = cur.x + dx, cur.y + dy
                    if not self.maze.in_bounds(nx, ny):
                        continue

                    cell = self.maze.grid[nx][ny]
                    if cell.type == CellType.WALL:
                        if cur.breaks_used < self.K and not visited[nx][ny][cur.breaks_used + 1]:
                            visited[nx][ny][cur.breaks_used + 1] = True
                            q.append(State(nx, ny, cur.breaks_used + 1))
                    else:
                        if not visited[nx][ny][cur.breaks_used]:
                            visited[nx][ny][cur.breaks_used] = True
                            q.append(State(nx, ny, cur.breaks_used))

                if self.maze.is_portal(cur.x, cur.y):
                    px, py = self.maze.exit_portal(cur.x, cur.y)
                    if not visited[px][py][cur.breaks_used]:
                        visited[px][py][cur.breaks_used] = True
                        q.append(State(px, py, cur.breaks_used))

            steps += 1

        return -1

    
    def shortest_path_with_path(self):
        visited = [[[False for _ in range(self.K + 1)]
                    for _ in range(self.maze.cols)]
                   for _ in range(self.maze.rows)]

        parent = {} 
        sx, sy = self.maze.start
        gx, gy = self.maze.goal

        q = deque()
        q.append((sx, sy, 0))
        visited[sx][sy][0] = True

        while q:
            x, y, b = q.popleft()

            if (x, y) == (gx, gy):
                
                path = []
                cur = (x, y, b)
                while cur in parent:
                    path.append((cur[0], cur[1]))
                    cur = parent[cur]
                path.append((sx, sy))
                path.reverse()

                return len(path) - 1, path

            
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x + dx, y + dy
                if not self.maze.in_bounds(nx, ny):
                    continue

                cell = self.maze.grid[nx][ny]

                if cell.type == CellType.WALL:
                    if b < self.K and not visited[nx][ny][b + 1]:
                        visited[nx][ny][b + 1] = True
                        parent[(nx, ny, b + 1)] = (x, y, b)
                        q.append((nx, ny, b + 1))
                else:
                    if not visited[nx][ny][b]:
                        visited[nx][ny][b] = True
                        parent[(nx, ny, b)] = (x, y, b)
                        q.append((nx, ny, b))

            
            if self.maze.is_portal(x, y):
                px, py = self.maze.exit_portal(x, y)
                if not visited[px][py][b]:
                    visited[px][py][b] = True
                    parent[(px, py, b)] = (x, y, b)
                    q.append((px, py, b))

        return None

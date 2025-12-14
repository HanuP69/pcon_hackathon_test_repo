import heapq
from .state import State
from ..core.maze import CellType


class Node:
    def __init__(self, x, y, breaks_used, g, f):
        self.x = x
        self.y = y
        self.breaks_used = breaks_used
        self.g = g
        self.f = f
        self.parent = None

    def __lt__(self, other):
        return self.f < other.f


class AStarSolver:
    def __init__(self, maze, k):
        self.maze = maze
        self.K = k
        self.expanded = 0

        self.best_g = [
            [[float('inf') for _ in range(k + 1)]
             for _ in range(maze.cols)]
            for _ in range(maze.rows)
        ]

    def h(self, x, y):
        return abs(x - self.maze.goal[0]) + abs(y - self.maze.goal[1])

    def shortest_path(self):
        pq = []

        sx, sy = self.maze.start
        start = Node(sx, sy, 0, 0, self.h(sx, sy))
        heapq.heappush(pq, start)
        self.best_g[sx][sy][0] = 0

        while pq:
            cur = heapq.heappop(pq)
            self.expanded += 1

            if cur.g > self.best_g[cur.x][cur.y][cur.breaks_used]:
                continue

            if (cur.x, cur.y) == self.maze.goal:
                path = []
                node = cur
                while node:
                    path.append((node.x, node.y))
                    node = node.parent
                path.reverse()
                return cur.g, path

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cur.x + dx, cur.y + dy
                if not self.maze.in_bounds(nx, ny):
                    continue

                cell = self.maze.grid[nx][ny]

                if cell.type == CellType.WALL:
                    if cur.breaks_used >= self.K:
                        continue
                    ng = cur.g + 1
                    nb = cur.breaks_used + 1
                else:
                    ng = cur.g + 1
                    nb = cur.breaks_used

                if ng < self.best_g[nx][ny][nb]:
                    self.best_g[nx][ny][nb] = ng
                    nxt = Node(nx, ny, nb, ng, ng + self.h(nx, ny))
                    nxt.parent = cur
                    heapq.heappush(pq, nxt)

            if self.maze.is_portal(cur.x, cur.y):
                px, py = self.maze.exit_portal(cur.x, cur.y)
                ng = cur.g + 1
                nb = cur.breaks_used

                if ng < self.best_g[px][py][nb]:
                    self.best_g[px][py][nb] = ng
                    nxt = Node(px, py, nb, ng, ng + self.h(px, py))
                    nxt.parent = cur
                    heapq.heappush(pq, nxt)

        return None

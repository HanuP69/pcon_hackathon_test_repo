import pygame
import base64
import sys

IS_WEB = sys.platform == "emscripten"
if IS_WEB:
    from platform import window

from web.state import GameState
from src.core.maze import Maze, CellType
from src.solver.bfs_solver import BFSSolver



CELL_SIZE = 25
GRID_SIZE = 20
GRID_ORIGIN = (50, 50)

BASE_TILES = [
    ("EMPTY", (255, 255, 255)),
    ("WALL",  (0, 0, 0)),
    ("START", (0, 200, 0)),
    ("GOAL",  (200, 0, 0)),
]

PORTAL_COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 0), (255, 0, 255),
    (0, 255, 255), (255, 128, 0),
    (128, 0, 255), (0, 128, 255),
    (128, 255, 0),
]

class EditorScreen:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Arial", 18)
        self.big_font = pygame.font.SysFont("Arial", 20, bold=True)

        self.grid = [[BASE_TILES[0][1] for _ in range(GRID_SIZE)]
                     for _ in range(GRID_SIZE)]

        self.selected = BASE_TILES[1][1]
        self.message = ""
        self.seed = None
        
        self.k_value = 3 

    def update(self):
        pass

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse(e.pos)

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.game.switch(GameState.MODE)

                elif e.key == pygame.K_p:
                    self.publish()


                elif e.key == pygame.K_UP:
                    self.k_value = min(10, self.k_value + 1)
                elif e.key == pygame.K_DOWN:
                    self.k_value = max(0, self.k_value - 1)

  
    def handle_mouse(self, pos):
        x, y = pos


        px, py = 600, 80
        for _, color in BASE_TILES:
            if pygame.Rect(px, py, 30, 30).collidepoint(pos):
                self.selected = color
                return
            py += 35

        for color in PORTAL_COLORS:
            if pygame.Rect(px, py, 30, 30).collidepoint(pos):
                self.selected = color
                return
            py += 35

        gx = (x - GRID_ORIGIN[0]) // CELL_SIZE
        gy = (y - GRID_ORIGIN[1]) // CELL_SIZE

        if not (0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE):
            return


        if self.selected == BASE_TILES[2][1] or self.selected == BASE_TILES[3][1]:
            self.clear_color(self.selected)

        if self.selected in PORTAL_COLORS:
            if self.count_color(self.selected) >= 2:
                self.message = "Portal color already used twice"
                return

        self.grid[gx][gy] = self.selected

    def clear_color(self, color):
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if self.grid[i][j] == color:
                    self.grid[i][j] = BASE_TILES[0][1]

    def count_color(self, color):
        return sum(
            self.grid[i][j] == color
            for i in range(GRID_SIZE)
            for j in range(GRID_SIZE)
        )


    def publish(self):

        if self.count_color(BASE_TILES[2][1]) != 1 or \
           self.count_color(BASE_TILES[3][1]) != 1:
            self.message = "Need exactly one START and one GOAL"
            return

        for c in PORTAL_COLORS:
            cnt = self.count_color(c)
            if cnt not in (0, 2):
                self.message = "❌ Each portal color must appear exactly twice"
                return

        maze = Maze(GRID_SIZE, GRID_SIZE)
        portal_map = {}
        char_grid = []


        for j in range(GRID_SIZE):    
            for i in range(GRID_SIZE):
                color = self.grid[i][j]
                cell = maze.grid[i][j]

                char_code = "."

                if color == BASE_TILES[1][1]: 
                    cell.type = CellType.WALL
                    char_code = "#"
                elif color == BASE_TILES[0][1]:
                    cell.type = CellType.EMPTY
                    char_code = "."
                elif color == BASE_TILES[2][1]:
                    cell.type = CellType.START
                    maze.start = (i, j)
                    char_code = "S"
                elif color == BASE_TILES[3][1]:
                    cell.type = CellType.GOAL
                    maze.goal = (i, j)
                    char_code = "G"
                else:                          
                    if color in PORTAL_COLORS:
                        pid = PORTAL_COLORS.index(color)
                        cell.type = CellType.PORTAL
                        cell.portal_id = pid
                        portal_map.setdefault(pid, []).append((i, j))
                        char_code = chr(ord('a') + pid)
                
                char_grid.append(char_code)

        for pid, cells in portal_map.items():
            maze.portals[pid] = (cells[0], cells[1])

        solver = BFSSolver(maze, self.k_value)
        
        if solver.shortest_path() == -1:
            self.message = f"❌ Unsolvable (even with K={self.k_value})"
            return 

        rle = []
        count = 1
        for k in range(1, len(char_grid)):
            if char_grid[k] == char_grid[k - 1]:
                count += 1
            else:
                rle.append(f"{count}{char_grid[k - 1]}")
                count = 1
        rle.append(f"{count}{char_grid[-1]}")

        payload = "".join(rle)
        encoded = base64.urlsafe_b64encode(payload.encode()).decode()

        self.seed = f"MS2|{GRID_SIZE}x{GRID_SIZE}|{self.k_value}|{encoded}"

        if IS_WEB:
            try:

                window.prompt("Copy this seed (Ctrl+C):", self.seed)
                self.message = "✅ Seed Ready! (Copy from popup)"
            except Exception as err:
                print(f"ERROR: {err}")
                self.message = "✅ Seed Generated (Check Console)"
    

    def draw(self):
        self.game.screen.fill((30, 30, 30))

        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                x = GRID_ORIGIN[0] + i * CELL_SIZE
                y = GRID_ORIGIN[1] + j * CELL_SIZE
                color = self.grid[i][j]

                pygame.draw.rect(self.game.screen, color, (x, y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(self.game.screen, (60, 60, 60), (x, y, CELL_SIZE, CELL_SIZE), 1)

                if color == BASE_TILES[2][1]:
                    self.game.screen.blit(self.big_font.render("S", True, 0), (x+7, y+4))
                elif color == BASE_TILES[3][1]:
                    self.game.screen.blit(self.big_font.render("G", True, 0), (x+7, y+4))

        px, py = 600, 80
        
        for name, color in BASE_TILES:
            pygame.draw.rect(self.game.screen, color, (px, py, 30, 30))
            if self.selected == color:
                pygame.draw.rect(self.game.screen, (255, 255, 255), (px-2, py-2, 34, 34), 2)
            py += 35

        py += 10
        for color in PORTAL_COLORS:
            pygame.draw.rect(self.game.screen, color, (px, py, 30, 30))
            if self.selected == color:
                pygame.draw.rect(self.game.screen, (255, 255, 255), (px-2, py-2, 34, 34), 2)
            py += 35

        k_txt = self.font.render(f"Max Breaks (K): {self.k_value}", True, (255, 255, 0))
        self.game.screen.blit(k_txt, (600, 20))
        hint = self.font.render("(UP/DOWN)", True, (150, 150, 150))
        self.game.screen.blit(hint, (600, 45))

        help_txt = self.font.render("Press P to Publish", True, (150, 150, 150))
        self.game.screen.blit(help_txt, (50, 20))

        if self.message:
            msg = self.font.render(self.message, True, (255, 255, 0))
            self.game.screen.blit(msg, (50, 560))

        if self.seed:
            self.game.screen.blit(self.font.render("Seed Generated:", True, (200,200,200)), (50, 590))
            self.game.screen.blit(self.font.render(self.seed[:60]+"...", True, (100,200,255)), (50, 615))
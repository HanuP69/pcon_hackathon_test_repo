import pygame
import time
import base64
import random


from web.clipboard import copy, paste  

from web.state import GameState
from web.leaderboard import add_score, get_scores
from web.renderer import draw_maze, draw_player, draw_path
from web.player import Player

from src.tools.dataset_generator import generate_maze
from src.solver.AStarSolver import AStarSolver
from src.solver.bfs_solver import BFSSolver


class WelcomeScreen:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Arial", 32)
        self.start_time = pygame.time.get_ticks()

    def handle_events(self):
        pass

    def update(self):
        if pygame.time.get_ticks() - self.start_time > 2000:
            self.game.switch(GameState.NAME)

    def draw(self):
        self.game.screen.fill((30, 30, 30))
        text = self.font.render("Welcome to Maze Solver", True, (255, 255, 255))
        self.game.screen.blit(text, (220, 360))


class NameScreen:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Arial", 28)
        self.name = ""

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                
                is_ctrl = (e.mod & pygame.KMOD_CTRL)

                if e.key == pygame.K_RETURN and self.name:
                    self.game.player_name = self.name
                    
                    if hasattr(self.game, 'restart_maze') and self.game.restart_maze:
                        self.game.switch(GameState.PLAY, custom_maze=self.game.restart_maze, fixed_k=self.game.restart_k)
                        self.game.restart_maze = None
                    else:
                        self.game.switch(GameState.MODE)

                elif e.key == pygame.K_BACKSPACE:
                    self.name = self.name[:-1]

                elif is_ctrl and e.key == pygame.K_v:
                    pasted_text = paste()
                    if pasted_text:
                        remaining_space = 12 - len(self.name)
                        if remaining_space > 0:
                            self.name += pasted_text[:remaining_space]

                elif is_ctrl and e.key == pygame.K_c:
                    copy(self.name) 


                elif e.unicode.isprintable() and len(self.name) < 12 and not is_ctrl:
                    self.name += e.unicode

    def update(self):
        pass

    def draw(self):
        self.game.screen.fill((20, 20, 20))
        t1 = self.font.render("Enter your name:", True, (255, 255, 255))
        t2 = self.font.render(self.name, True, (255, 255, 0))
        self.game.screen.blit(t1, (250, 300))
        self.game.screen.blit(t2, (250, 350))


class ModeScreen:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Arial", 28)

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_1:
                    self.game.mode = "CLASSIC"
                    self.game.switch(GameState.PLAY)
                elif e.key == pygame.K_2:
                    self.game.mode = "BREAK"
                    self.game.switch(GameState.PLAY)
                elif e.key == pygame.K_3:
                    self.game.switch(GameState.EDITOR)
                elif e.key == pygame.K_4:
                    self.game.switch(GameState.LOAD)

    def update(self):
        pass

    def draw(self):
        self.game.screen.fill((0, 0, 0))
        lines = [
            "1 : Classic Mode (No Breaks)",
            "2 : Break Mode (Random K)",
            "3 : Editor Mode (Create Map)",
            "4 : Play from Seed (Friend Map)",
        ]
        y = 300
        for line in lines:
            t = self.font.render(line, True, (255, 255, 255))
            self.game.screen.blit(t, (180, y))
            y += 40


class PlayScreen:
    def __init__(self, game, custom_maze=None, fixed_k=None):
        self.game = game
        self.font = pygame.font.SysFont("Arial", 24)
        self.table_font = pygame.font.SysFont("Arial", 16) 
        self.CELL_SIZE = 20

        self.start_time = time.time()
        self.end_time = None

        self.show_astar = False
        self.show_bfs = False
        self.show_leaderboard = False

        if custom_maze:
            self.maze = custom_maze
            self.K = fixed_k if fixed_k is not None else 0
            self._solve_and_ready()
        else:
            self.generate_new_map()

    def generate_new_map(self):
        while True:
            self.K = 0 if self.game.mode == "CLASSIC" else random.randint(1, 5)
            self.maze = generate_maze(21, 21, 3, 15)
            bfs = BFSSolver(self.maze, self.K)
            if bfs.shortest_path() != -1:
                break 
        self._solve_and_ready()

    def _solve_and_ready(self):
        bfs = BFSSolver(self.maze, self.K)
        res = bfs.shortest_path_with_path()
        self.bfs_dist, self.bfs_path = res if res else (0, [])

        astar = AStarSolver(self.maze, self.K)
        res = astar.shortest_path()
        self.astar_dist, self.astar_path = res if res else (0, [])

        self.build_seed()
        self.player = Player(self.maze.start, self.K)
        
        self.finished = False
        self.score = None

    def build_seed(self):
        chars = []
        for j in range(self.maze.rows):
            for i in range(self.maze.cols):
                cell = self.maze.grid[i][j]
                if cell.type.name == "WALL": chars.append("#")
                elif cell.type.name == "EMPTY": chars.append(".")
                elif cell.type.name == "START": chars.append("S")
                elif cell.type.name == "GOAL": chars.append("G")
                else: chars.append(chr(ord("a") + cell.portal_id))

        raw = "".join(chars).encode()
        encoded = base64.urlsafe_b64encode(raw).decode()
        self.game.current_seed = f"MS2|{self.maze.cols}x{self.maze.rows}|{self.K}|{encoded}"

    def save_to_leaderboard(self):
        add_score(
            self.game.current_seed,
            self.game.player_name,
            self.score,
            self.time_taken
        )

    def handle_events(self):
        for e in pygame.event.get():
            if e.type != pygame.KEYDOWN:
                continue

            if e.key == pygame.K_TAB:
                self.show_leaderboard = not self.show_leaderboard
                return
            
            if e.key == pygame.K_r:
                self.game.restart_maze = self.maze
                self.game.restart_k = self.K
                self.game.switch(GameState.NAME)
                return
            
            if e.key == pygame.K_t:
                self.game.restart_maze = None
                self.game.switch(GameState.NAME)
                return

            if self.finished:
                return

            shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
            
            if e.key in (pygame.K_w, pygame.K_UP):
                self.player.try_move(-1, 0, self.maze) if not shift else self.player.break_wall(-1, 0, self.maze)
            elif e.key in (pygame.K_s, pygame.K_DOWN):
                self.player.try_move(1, 0, self.maze) if not shift else self.player.break_wall(1, 0, self.maze)
            elif e.key in (pygame.K_a, pygame.K_LEFT):
                self.player.try_move(0, -1, self.maze) if not shift else self.player.break_wall(0, -1, self.maze)
            elif e.key in (pygame.K_d, pygame.K_RIGHT):
                self.player.try_move(0, 1, self.maze) if not shift else self.player.break_wall(0, 1, self.maze)

            elif e.key == pygame.K_RETURN:
                self.player.use_portal(self.maze)

            elif e.key == pygame.K_h:
                self.show_astar = not self.show_astar

            elif e.key == pygame.K_b:
                self.show_bfs = not self.show_bfs

    def update(self):
        if not self.finished and (self.player.x, self.player.y) == self.maze.goal:
            self.finished = True
            self.end_time = time.time()
            self.time_taken = round(self.end_time - self.start_time, 2)
            if self.player.steps > 0:
                self.score = (self.bfs_dist / self.player.steps) * 100
            else:
                self.score = 0
            self.save_to_leaderboard()

    def draw(self):
        self.game.screen.fill((50, 50, 50))

        draw_maze(self.game.screen, self.maze, self.font)

        for i in range(self.maze.cols):
            for j in range(self.maze.rows):
                x = i * self.CELL_SIZE
                y = j * self.CELL_SIZE
                pygame.draw.rect(self.game.screen, (80, 80, 80), (x, y, self.CELL_SIZE, self.CELL_SIZE), 1)

        if self.show_bfs:
            draw_path(self.game.screen, self.bfs_path, color=(255, 105, 180))
        if self.show_astar:
            draw_path(self.game.screen, self.astar_path, color=(0, 180, 255))
        if self.finished:
            draw_path(self.game.screen, self.player.path, color=(255, 215, 0))

        draw_player(self.game.screen, self.player)

        hud_y = self.maze.rows * self.CELL_SIZE + 10
        status = "FINISHED!" if self.finished else "PLAYING"
        current_time_val = self.time_taken if self.finished else time.time() - self.start_time

        hud_text = (
            f"{status} | Time: {current_time_val:.1f}s | "
            f"Steps: {self.player.steps} | Breaks: {self.player.breaks_left}/{self.player.max_breaks}"
        )
        
        hud = self.font.render(hud_text, True, (255, 255, 255))
        self.game.screen.blit(hud, (10, hud_y))

        if self.finished and self.score is not None:
             score_txt = self.font.render(f"Final Score: {self.score:.2f} | Time: {self.time_taken}s", True, (255, 215, 0))
             self.game.screen.blit(score_txt, (10, hud_y + 30))

        panel_x = 520
        panel_y = 50 

        if self.show_leaderboard:
            scores = get_scores(self.game.current_seed)
            title = self.font.render("Leaderboard (TAB)", True, (255, 255, 0))
            self.game.screen.blit(title, (panel_x, panel_y))
            panel_y += 35

            if not scores:
                self.game.screen.blit(self.font.render("No scores yet.", True, (200,200,200)), (panel_x, panel_y))
            else:
                x_rank, x_name, x_score, x_time = panel_x, panel_x + 35, panel_x + 160, panel_x + 220
                head_col = (255, 215, 0)
                
                self.game.screen.blit(self.table_font.render("#", True, head_col), (x_rank, panel_y))
                self.game.screen.blit(self.table_font.render("NAME", True, head_col), (x_name, panel_y))
                self.game.screen.blit(self.table_font.render("SCR", True, head_col), (x_score, panel_y))
                self.game.screen.blit(self.table_font.render("TIME", True, head_col), (x_time, panel_y))

                panel_y += 25
                pygame.draw.line(self.game.screen, (100, 100, 100), (panel_x, panel_y-5), (panel_x+270, panel_y-5), 1)

                for i, s in enumerate(scores[:12]):
                    name_disp = s['name']
                    if len(name_disp) > 10: name_disp = name_disp[:9] + ".."
                    row_col = (200, 255, 200) if i == 0 else (220, 220, 220)

                    self.game.screen.blit(self.table_font.render(str(i+1), True, row_col), (x_rank, panel_y))
                    self.game.screen.blit(self.table_font.render(name_disp, True, row_col), (x_name, panel_y))
                    self.game.screen.blit(self.table_font.render(f"{s['score']:.1f}", True, row_col), (x_score, panel_y))
                    self.game.screen.blit(self.table_font.render(f"{s['time']:.1f}s", True, row_col), (x_time, panel_y))

                    panel_y += 20
        else:
            def legend(color, text, y):
                pygame.draw.rect(self.game.screen, color, (panel_x, y, 20, 20))
                t = self.font.render(text, True, (230, 230, 230))
                self.game.screen.blit(t, (panel_x + 30, y))

            legend((255, 105, 180), "BFS (B)", panel_y)
            legend((0, 180, 255), "A* (H)", panel_y + 30)
            legend((255, 215, 0), "Path", panel_y + 60)

            controls = [
                "", "Controls:", "WASD: Move", "SHIFT+Move: Break", "ENTER: Portal",
                "TAB: Leaderboard", "R: Retake (Same Map)", "T: New Map (New Name)"
            ]
            cy = panel_y + 100
            for line in controls:
                txt = self.font.render(line, True, (220, 220, 220))
                self.game.screen.blit(txt, (panel_x, cy))
                cy += 22
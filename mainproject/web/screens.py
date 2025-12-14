import pygame
import time
import base64
import random

from web.renderer import draw_maze, draw_player, draw_path, update_animation
from web.clipboard import copy, paste  
from web.state import GameState
from web.leaderboard import add_score, get_scores
from web.player import Player

from src.tools.dataset_generator import generate_maze
from src.solver.AStarSolver import AStarSolver
from src.solver.bfs_solver import BFSSolver


class WelcomeScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.subtitle_font = pygame.font.SysFont("Arial", 24)
        self.start_time = pygame.time.get_ticks()
        self.alpha = 0

    def handle_events(self):
        pass

    def update(self):
 
        elapsed = pygame.time.get_ticks() - self.start_time
        self.alpha = min(255, elapsed // 8)
        
        if elapsed > 2000:
            self.game.switch(GameState.NAME)

    def draw(self):
        self.game.screen.fill((135, 206, 235))
        for i in range(800):
            color = (135 - i//10, 206 - i//15, 235 - i//20)
            pygame.draw.line(self.game.screen, color, (0, i), (800, i))
        
        title_text = "Maze Solver"
        shadow = self.title_font.render(title_text, True, (0, 0, 0))
        title = self.title_font.render(title_text, True, (255, 255, 255))
        
        shadow_rect = shadow.get_rect(center=(402, 352))
        title_rect = title.get_rect(center=(400, 350))
        
        shadow.set_alpha(self.alpha)
        title.set_alpha(self.alpha)
        
        self.game.screen.blit(shadow, shadow_rect)
        self.game.screen.blit(title, title_rect)
        
        subtitle = self.subtitle_font.render("Find the fish, brave cat!", True, (255, 255, 255))
        subtitle.set_alpha(self.alpha)
        subtitle_rect = subtitle.get_rect(center=(400, 420))
        self.game.screen.blit(subtitle, subtitle_rect)


class NameScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.input_font = pygame.font.SysFont("Arial", 32)
        self.hint_font = pygame.font.SysFont("Arial", 18)
        self.name = ""
        self.cursor_visible = True
        self.cursor_timer = 0

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
        self.cursor_timer += 1
        if self.cursor_timer > 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self):
        self.game.screen.fill((135, 206, 235))
        for i in range(800):
            color = (135 - i//10, 206 - i//15, 235 - i//20)
            pygame.draw.line(self.game.screen, color, (0, i), (800, i))
        
        title = self.title_font.render("Enter Your Name", True, (255, 255, 255))
        title_rect = title.get_rect(center=(400, 280))
        
        shadow = self.title_font.render("Enter Your Name", True, (0, 0, 0))
        shadow_rect = shadow.get_rect(center=(402, 282))
        self.game.screen.blit(shadow, shadow_rect)
        self.game.screen.blit(title, title_rect)
        
        box_rect = pygame.Rect(250, 350, 300, 50)
        pygame.draw.rect(self.game.screen, (255, 255, 255), box_rect)
        pygame.draw.rect(self.game.screen, (100, 149, 237), box_rect, 3)
        
        cursor = "|" if self.cursor_visible else ""
        name_text = self.input_font.render(self.name + cursor, True, (0, 0, 0))
        name_rect = name_text.get_rect(center=(400, 375))
        self.game.screen.blit(name_text, name_rect)
        
        hint = self.hint_font.render("Press ENTER to continue (Max 12 characters)", True, (255, 255, 255))
        hint_rect = hint.get_rect(center=(400, 430))
        self.game.screen.blit(hint, hint_rect)


class ModeScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.SysFont("Arial", 40, bold=True)
        self.option_font = pygame.font.SysFont("Arial", 26)
        self.desc_font = pygame.font.SysFont("Arial", 18)
        self.selected = 0
        self.hover_alpha = 0

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
                elif e.key in (pygame.K_UP, pygame.K_w):
                    self.selected = (self.selected - 1) % 4
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.selected = (self.selected + 1) % 4
                elif e.key == pygame.K_RETURN:
                    if self.selected == 0:
                        self.game.mode = "CLASSIC"
                        self.game.switch(GameState.PLAY)
                    elif self.selected == 1:
                        self.game.mode = "BREAK"
                        self.game.switch(GameState.PLAY)
                    elif self.selected == 2:
                        self.game.switch(GameState.EDITOR)
                    elif self.selected == 3:
                        self.game.switch(GameState.LOAD)

    def update(self):
        self.hover_alpha = (self.hover_alpha + 5) % 255

    def draw(self):
        self.game.screen.fill((135, 206, 235))
        for i in range(800):
            color = (135 - i//10, 206 - i//15, 235 - i//20)
            pygame.draw.line(self.game.screen, color, (0, i), (800, i))
        
        title = self.title_font.render("Select Game Mode", True, (255, 255, 255))
        title_rect = title.get_rect(center=(400, 150))
        shadow = self.title_font.render("Select Game Mode", True, (0, 0, 0))
        shadow_rect = shadow.get_rect(center=(402, 152))
        self.game.screen.blit(shadow, shadow_rect)
        self.game.screen.blit(title, title_rect)
        
        options = [
            ("1", "Classic Mode", "No wall breaking allowed"),
            ("2", "Break Mode", "Break walls with random K value"),
            ("3", "Editor Mode", "Create your own maze"),
            ("4", "Load Seed", "Play a friend's maze"),
        ]
        
        y_start = 250
        for i, (key, name, desc) in enumerate(options):
            y = y_start + i * 100
            
            card_rect = pygame.Rect(150, y, 500, 80)
            card_color = (255, 255, 255) if i == self.selected else (240, 240, 240)
            
            if i == self.selected:
                glow = pygame.Surface((504, 84), pygame.SRCALPHA)
                glow_alpha = int(abs(self.hover_alpha - 127) + 50)
                pygame.draw.rect(glow, (100, 149, 237, glow_alpha), (0, 0, 504, 84), border_radius=10)
                self.game.screen.blit(glow, (148, y - 2))
            
            pygame.draw.rect(self.game.screen, card_color, card_rect, border_radius=8)
            pygame.draw.rect(self.game.screen, (100, 149, 237), card_rect, 3, border_radius=8)
            
            key_circle = pygame.Rect(170, y + 20, 40, 40)
            pygame.draw.circle(self.game.screen, (100, 149, 237), key_circle.center, 20)
            key_text = self.option_font.render(key, True, (255, 255, 255))
            key_rect = key_text.get_rect(center=key_circle.center)
            self.game.screen.blit(key_text, key_rect)
            
            name_text = self.option_font.render(name, True, (0, 0, 0))
            self.game.screen.blit(name_text, (230, y + 15))
            
            desc_text = self.desc_font.render(desc, True, (100, 100, 100))
            self.game.screen.blit(desc_text, (230, y + 45))
        
        hint = self.desc_font.render("Use number keys or arrow keys + ENTER", True, (255, 255, 255))
        hint_rect = hint.get_rect(center=(400, 730))
        self.game.screen.blit(hint, hint_rect)


class PlayScreen:
    def __init__(self, game, custom_maze=None, fixed_k=None):
        self.game = game
        self.title_font = pygame.font.SysFont("Arial", 28, bold=True)
        self.hud_font = pygame.font.SysFont("Arial", 20)
        self.table_font = pygame.font.SysFont("Arial", 16)
        self.small_font = pygame.font.SysFont("Arial", 14)
        self.CELL_SIZE = 32
        
        self.maze_offset_x = 0  
        self.maze_offset_y = 20  
        
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
            self.maze = generate_maze(15, 15, 3, 15)
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
        
        maze_width = self.maze.cols * self.CELL_SIZE
        self.maze_offset_x = (800 - maze_width) // 2
        
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
            
            if e.key == pygame.K_ESCAPE:
                self.game.switch(GameState.MODE)
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
        update_animation()
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
        self.game.screen.fill((135, 206, 235))
        

  
        maze_width = self.maze.cols * self.CELL_SIZE
        maze_height = self.maze.rows * self.CELL_SIZE
        maze_surface = pygame.Surface((maze_width, maze_height))
        maze_surface.fill((135, 206, 235))
        
        temp_screen = self.game.screen
        self.game.screen = maze_surface
        
        draw_maze(maze_surface, self.maze, self.hud_font)
        
        for i in range(self.maze.cols):
            for j in range(self.maze.rows):
                x = i * self.CELL_SIZE
                y = j * self.CELL_SIZE
                pygame.draw.rect(maze_surface, (200, 200, 200), (x, y, self.CELL_SIZE, self.CELL_SIZE), 1)
        
        if self.show_bfs:
            draw_path(maze_surface, self.bfs_path, color=(255, 105, 180))
        if self.show_astar:
            draw_path(maze_surface, self.astar_path, color=(0, 180, 255))
        if self.finished:
            draw_path(maze_surface, self.player.path, color=(255, 215, 0))
        
        draw_player(maze_surface, self.player)
        
        self.game.screen = temp_screen
        self.game.screen.fill((135, 206, 235))
        self.game.screen.blit(maze_surface, (self.maze_offset_x, self.maze_offset_y))
        
        panel_top = self.maze_offset_y + maze_height + 20
        

        if self.finished:
            status = self.title_font.render("FINISHED!", True, (255, 255, 255))
        else:
            status = self.title_font.render("PLAYING", True, (255, 255, 255))
        

        shadow = self.title_font.render(status.get_rect().width * " ", True, (0, 0, 0))
        self.game.screen.blit(shadow, (42, panel_top + 2))
        self.game.screen.blit(status, (40, panel_top))
        
 
        stats_y = panel_top + 40
        current_time_val = self.time_taken if self.finished else time.time() - self.start_time
        
        self.draw_stat_box(40, stats_y, 100, 60, "Time", f"{current_time_val:.1f}s")
        self.draw_stat_box(160, stats_y, 100, 60, "Steps", str(self.player.steps))
        
        break_color = (255, 100, 100) if self.player.breaks_left == 0 else (100, 255, 100)
        self.draw_stat_box(280, stats_y, 120, 60, "Breaks", 
                           f"{self.player.breaks_left}/{self.player.max_breaks}", break_color)
        
        if self.finished and self.score is not None:
            self.draw_stat_box(40, stats_y + 80, 140, 60, "Score", f"{self.score:.1f}", (255, 215, 0))
        
    
        panel_x = 440
        panel_y = panel_top
        
        if self.show_leaderboard:
            self.draw_leaderboard(panel_x, panel_y)
        else:
            self.draw_controls(panel_x, panel_y)

    def draw_stat_box(self, x, y, width, height, label, value, accent=(100, 149, 237)):

        box = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.game.screen, (255, 255, 255), box, border_radius=5)
        pygame.draw.rect(self.game.screen, accent, box, 2, border_radius=5)

        label_text = self.small_font.render(label, True, (100, 100, 100))
        self.game.screen.blit(label_text, (x + 5, y + 5))

        value_text = self.hud_font.render(str(value), True, (0, 0, 0))
        value_rect = value_text.get_rect(center=(x + width//2, y + height - 20))
        self.game.screen.blit(value_text, value_rect)

    def draw_leaderboard(self, x, y):

        panel = pygame.Rect(x - 10, y - 10, 330, 280)
        pygame.draw.rect(self.game.screen, (255, 255, 255), panel, border_radius=10)
        pygame.draw.rect(self.game.screen, (100, 149, 237), panel, 3, border_radius=10)

        title = self.title_font.render("🏆 Leaderboard", True, (100, 149, 237))
        self.game.screen.blit(title, (x, y))
        y += 40
        
        scores = get_scores(self.game.current_seed)
        
        if not scores:
            no_scores = self.hud_font.render("No scores yet!", True, (150, 150, 150))
            self.game.screen.blit(no_scores, (x + 60, y + 50))
        else:
 
            headers = ["#", "NAME", "SCORE", "TIME"]
            x_positions = [x, x + 30, x + 130, x + 220]
            
            for i, header in enumerate(headers):
                header_text = self.table_font.render(header, True, (100, 149, 237))
                self.game.screen.blit(header_text, (x_positions[i], y))
            
            y += 25
            pygame.draw.line(self.game.screen, (200, 200, 200), (x, y), (x + 300, y), 2)
            y += 10

            for i, s in enumerate(scores[:8]):
                name_disp = s['name']
                if len(name_disp) > 10:
                    name_disp = name_disp[:9] + ".."

                if i == 0:
                    row_color = (255, 215, 0)  
                elif i == 1:
                    row_color = (192, 192, 192) 
                elif i == 2:
                    row_color = (205, 127, 50) 
                else:
                    row_color = (80, 80, 80)
     
                rank_text = self.table_font.render(str(i + 1), True, row_color)
                self.game.screen.blit(rank_text, (x_positions[0], y))
    
                name_text = self.table_font.render(name_disp, True, row_color)
                self.game.screen.blit(name_text, (x_positions[1], y))
       
                score_text = self.table_font.render(f"{s['score']:.1f}", True, row_color)
                self.game.screen.blit(score_text, (x_positions[2], y))
 
                time_text = self.table_font.render(f"{s['time']:.1f}s", True, row_color)
                self.game.screen.blit(time_text, (x_positions[3], y))
                
                y += 22

        hint = self.small_font.render("Press TAB to close", True, (150, 150, 150))
        self.game.screen.blit(hint, (x + 80, y + 10))

    def draw_controls(self, x, y):

        panel = pygame.Rect(x - 10, y - 10, 330, 280)
        pygame.draw.rect(self.game.screen, (255, 255, 255), panel, border_radius=10)
        pygame.draw.rect(self.game.screen, (100, 149, 237), panel, 3, border_radius=10)
   
        title = self.title_font.render("Controls", True, (100, 149, 237))
        self.game.screen.blit(title, (x, y))
        y += 40

        legends = [
            ((255, 105, 180), "BFS Path (B)"),
            ((0, 180, 255), "A* Path (H)"),
            ((255, 215, 0), "Your Path"),
        ]
        
        for color, text in legends:
            pygame.draw.circle(self.game.screen, color, (x + 10, y + 10), 8)
            legend_text = self.hud_font.render(text, True, (80, 80, 80))
            self.game.screen.blit(legend_text, (x + 30, y + 2))
            y += 28
        
        y += 10 # 
        
  
        controls = [
            ("WASD", "Move"),
            ("SHIFT+MOVE", "Break"), 
            ("ENTER", "Portal"),
            ("TAB", "Scores"),
            ("ESC", "Menu"),
            ("R", "Retry"),
            ("T", "New Maze"),
        ]
        
        start_y = y 
        col_width = 160 
        
        for i, (key, action) in enumerate(controls):
            col = i%2 
            row = i//2
            

            current_x = x + (col * col_width)
            current_y = start_y + (row * 28)
            

            key_width = max(50, len(key) * 9 + 10) 
            key_rect = pygame.Rect(current_x, current_y, key_width, 22)
            pygame.draw.rect(self.game.screen, (100, 149, 237), key_rect, border_radius=4)
            
            key_text = self.small_font.render(key, True, (255, 255, 255))
            key_text_rect = key_text.get_rect(center=key_rect.center)
            self.game.screen.blit(key_text, key_text_rect)

            action_text = self.small_font.render(action, True, (80, 80, 80))
            self.game.screen.blit(action_text, (current_x + key_width + 8, current_y + 4))
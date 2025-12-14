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

COL_HUD_BG = (15, 23, 42, 240) 
COL_ACCENT = (56, 189, 248)    
COL_TEXT = (226, 232, 240)     
COL_GOLD = (250, 204, 21)
COL_DANGER = (239, 68, 68)
COL_SUCCESS = (34, 197, 94)
class WelcomeScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.SysFont("Arial", 60, bold=True)
        self.subtitle_font = pygame.font.SysFont("Arial", 24)
        
        self.blink_timer = 0
        self.show_text = True

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                self.game.switch(GameState.NAME)

    def update(self):
        self.blink_timer += 1
        if self.blink_timer > 30:
            self.show_text = not self.show_text
            self.blink_timer = 0

    def draw(self):
        self.game.screen.fill((0, 0, 0)) 

        title_surf = self.title_font.render("CAT & MAZE", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(400, 350))
        self.game.screen.blit(title_surf, title_rect)

        if self.show_text:
            sub_surf = self.subtitle_font.render("Press any key to start", True, (200, 200, 200))
            sub_rect = sub_surf.get_rect(center=(400, 450))
            self.game.screen.blit(sub_surf, sub_rect)


class NameScreen:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.input_font = pygame.font.SysFont("Arial", 32)
        self.hint_font = pygame.font.SysFont("Arial", 18)
        self.name = ""
        self.cursor_visible = True
        self.cursor_timer = 0
        
        try:
            self.bg_image = pygame.image.load("assets/bg.png")
            self.bg_image = pygame.transform.scale(self.bg_image, (800, 800))
            self.has_bg = True
        except Exception:
            self.has_bg = False

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
        if self.has_bg:
            self.game.screen.blit(self.bg_image, (0, 0))
            overlay = pygame.Surface((800, 800), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0, 0, 0, 100), (0, 0, 800, 800))
            self.game.screen.blit(overlay, (0, 0))
        else:
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
        
        try:
            self.bg_image = pygame.image.load("assets/bg.png")
            self.bg_image = pygame.transform.scale(self.bg_image, (800, 800))
            self.has_bg = True
        except Exception as e:
            self.has_bg = False

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
        if self.has_bg:
            self.game.screen.blit(self.bg_image, (0, 0))
            overlay = pygame.Surface((800, 800), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0, 0, 0, 120), (0, 0, 800, 800))
            self.game.screen.blit(overlay, (0, 0))
        else:
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
        
        self.font_title = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.font_hud_label = pygame.font.SysFont("Segoe UI", 12, bold=True)
        self.font_hud_val = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 16)
        self.font_mono = pygame.font.SysFont("Consolas", 14)
        
        self.CELL_SIZE = 32
        self.SCREEN_W, self.SCREEN_H = self.game.screen.get_size()
        
        self.start_time = time.time()
        self.total_pause_duration = 0
        self.pause_start_timestamp = 0
        self.paused = False 
        
        self.finished = False
        self.time_taken = 0
        
        self.show_astar = False
        self.show_bfs = False
        self.show_leaderboard = False
        self.show_controls = False 
        self.cached_scores = []

        self.bg_img = pygame.image.load("assets/playscreen_bg.png")
        self.bg_img = pygame.transform.scale(self.bg_img, (self.SCREEN_W, self.SCREEN_H))

        if custom_maze:
            self.maze = custom_maze
            self.K = fixed_k if fixed_k is not None else 0
            self._solve_and_ready()
        else:
            self.generate_new_map()

        self._recalculate_layout()

    def _recalculate_layout(self):
        maze_w = self.maze.cols * self.CELL_SIZE
        maze_h = self.maze.rows * self.CELL_SIZE
        self.maze_offset_x = (self.SCREEN_W - maze_w) // 2
        self.maze_offset_y = (self.SCREEN_H - maze_h) // 2 + 20 

    def generate_new_map(self):
        while True:
            self.K = 0 if self.game.mode == "CLASSIC" else random.randint(1, 5)
            self.maze = generate_maze(15, 15, 3, 15)
            bfs = BFSSolver(self.maze, self.K)
            if bfs.shortest_path() != -1:
                break 
        self._solve_and_ready()

    def _solve_and_ready(self):
        self.cached_scores = [] 
        self.finished = False
        self.score = None
        self.score_submitted = False
        
        self.start_time = time.time()
        self.total_pause_duration = 0
        self.paused = False
        self.time_taken = 0 # Reset here

        bfs = BFSSolver(self.maze, self.K)
        res = bfs.shortest_path_with_path()
        self.bfs_dist, self.bfs_path = res if res else (0, [])

        astar = AStarSolver(self.maze, self.K)
        res = astar.shortest_path()
        self.astar_dist, self.astar_path = res if res else (0, [])

        self.build_seed()
        self.player = Player(self.maze.start, self.K)
        self._recalculate_layout()

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

    def toggle_pause(self, state=None):
        new_state = not self.paused if state is None else state
        if new_state == self.paused: return 

        self.paused = new_state
        if self.paused:
            self.pause_start_timestamp = time.time()
        else:
            self.total_pause_duration += (time.time() - self.pause_start_timestamp)

    def get_display_time(self):

        if self.finished: 
            return self.time_taken
            
        now = time.time()
        if self.paused:
            return self.pause_start_timestamp - self.start_time - self.total_pause_duration
        else:
            return now - self.start_time - self.total_pause_duration

    def _draw_loading(self, msg="Loading..."):
        self.draw() 
        overlay = pygame.Surface((self.SCREEN_W, self.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.game.screen.blit(overlay, (0,0))
        txt = self.font_title.render(msg, True, COL_ACCENT)
        self.game.screen.blit(txt, txt.get_rect(center=(self.SCREEN_W//2, self.SCREEN_H//2)))
        pygame.display.flip()

    def handle_events(self):
        for e in pygame.event.get():
            if e.type != pygame.KEYDOWN: continue

            if e.key == pygame.K_ESCAPE:
                if self.show_leaderboard or self.show_controls:
                    self.show_leaderboard = False
                    self.show_controls = False
                    self.toggle_pause(False) 
                else:
                    self.game.switch(GameState.MODE)
                return

            if e.key == pygame.K_TAB:
                self.show_leaderboard = not self.show_leaderboard
                self.show_controls = False
                self.toggle_pause(self.show_leaderboard)
                
                if self.show_leaderboard:
                    self._draw_loading("Fetching Scores...")
                    try: self.cached_scores = get_scores(self.game.current_seed)
                    except: self.cached_scores = []
                return
            
            if e.key == pygame.K_c:
                self.show_controls = not self.show_controls
                self.show_leaderboard = False
                self.toggle_pause(self.show_controls)
                return

            if e.key == pygame.K_r:
                self.game.restart_maze = self.maze
                self.game.restart_k = self.K
                self.game.switch(GameState.NAME)
            elif e.key == pygame.K_t:
                self.game.restart_maze = None
                self.game.switch(GameState.NAME)

            if self.paused or self.finished:
                continue 

            shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
            if e.key in (pygame.K_w, pygame.K_UP): self.player.try_move(-1, 0, self.maze) if not shift else self.player.break_wall(-1, 0, self.maze)
            elif e.key in (pygame.K_s, pygame.K_DOWN): self.player.try_move(1, 0, self.maze) if not shift else self.player.break_wall(1, 0, self.maze)
            elif e.key in (pygame.K_a, pygame.K_LEFT): self.player.try_move(0, -1, self.maze) if not shift else self.player.break_wall(0, -1, self.maze)
            elif e.key in (pygame.K_d, pygame.K_RIGHT): self.player.try_move(0, 1, self.maze) if not shift else self.player.break_wall(0, 1, self.maze)
            elif e.key == pygame.K_RETURN: self.player.use_portal(self.maze)
            elif e.key == pygame.K_h: self.show_astar = not self.show_astar
            elif e.key == pygame.K_b: self.show_bfs = not self.show_bfs

    def update(self):
        if self.paused or self.finished: return
        
        update_animation()
        
        if (self.player.x, self.player.y) == self.maze.goal:

            final_time = self.get_display_time()
            self.time_taken = round(final_time, 2)
            self.finished = True
            
            if self.player.steps > 0:
                self.score = (self.bfs_dist / self.player.steps) * 100
            else:
                self.score = 0
            
            self._draw_loading("Submitting Score...")
            
            if not self.score_submitted:
                add_score(self.game.current_seed, self.game.player_name, self.score, self.time_taken)
                self.score_submitted = True
                try: self.cached_scores = get_scores(self.game.current_seed)
                except: self.cached_scores = []

            self.show_leaderboard = True
            self.toggle_pause(True)

    def draw(self):
        self.game.screen.blit(self.bg_img, (0, 0))
        s = pygame.Surface((self.SCREEN_W, self.SCREEN_H), pygame.SRCALPHA)
        s.fill((10, 15, 30, 180)) 
        self.game.screen.blit(s, (0,0))

        self._draw_maze_layer()
        self._draw_hud()
        self._draw_hints()

        if self.show_leaderboard:
            self._draw_overlay_bg()
            self._draw_leaderboard_modal()
        elif self.show_controls:
            self._draw_overlay_bg()
            self._draw_controls_modal()

    def _draw_maze_layer(self):
        maze_w = self.maze.cols * self.CELL_SIZE
        maze_h = self.maze.rows * self.CELL_SIZE
        maze_surf = pygame.Surface((maze_w, maze_h))
        maze_surf.fill((20, 25, 40)) 

        draw_maze(maze_surf, self.maze, self.font_mono)
        
        for i in range(self.maze.cols):
            for j in range(self.maze.rows):
                pygame.draw.rect(maze_surf, (255, 255, 255, 10), (i*32, j*32, 32, 32), 1)

        if self.show_bfs: draw_path(maze_surf, self.bfs_path, color=(236, 72, 153))
        if self.show_astar: draw_path(maze_surf, self.astar_path, color=(6, 182, 212))
        if self.finished: draw_path(maze_surf, self.player.path, color=COL_GOLD)
        
        draw_player(maze_surf, self.player)

        pygame.draw.rect(self.game.screen, (0, 0, 0, 150), (self.maze_offset_x+8, self.maze_offset_y+8, maze_w, maze_h), border_radius=4)
        pygame.draw.rect(self.game.screen, (71, 85, 105), (self.maze_offset_x-2, self.maze_offset_y-2, maze_w+4, maze_h+4), 2)
        self.game.screen.blit(maze_surf, (self.maze_offset_x, self.maze_offset_y))

    def _draw_hud(self):
        hud_h = 70
        s = pygame.Surface((self.SCREEN_W, hud_h), pygame.SRCALPHA)
        s.fill(COL_HUD_BG)
        self.game.screen.blit(s, (0, 0))
        pygame.draw.line(self.game.screen, (56, 189, 248, 100), (0, hud_h), (self.SCREEN_W, hud_h), 1)

        if self.finished:
            status_txt, status_col = "LEVEL COMPLETE", COL_SUCCESS
        elif self.paused:
            status_txt, status_col = "PAUSED", COL_GOLD
        else:
            status_txt, status_col = "EXPLORING", COL_ACCENT

        self._draw_hud_pill(40, "TIME", f"{self.get_display_time():.1f}s")
        self._draw_hud_pill(160, "STEPS", str(self.player.steps))
        
        title = self.font_title.render(status_txt, True, status_col)
        self.game.screen.blit(title, title.get_rect(center=(self.SCREEN_W // 2, hud_h // 2)))

        brk_col = COL_DANGER if self.player.breaks_left == 0 else COL_SUCCESS
        self._draw_hud_pill(self.SCREEN_W - 240, "BREAKS", f"{self.player.breaks_left}/{self.player.max_breaks}", brk_col)
        
        if self.finished and self.score is not None:
             self._draw_hud_pill(self.SCREEN_W - 120, "SCORE", f"{self.score:.0f}", COL_GOLD)

    def _draw_hud_pill(self, x, label, val, color=COL_ACCENT):
        self.game.screen.blit(self.font_hud_label.render(label, True, (148, 163, 184)), (x, 15))
        self.game.screen.blit(self.font_hud_val.render(str(val), True, color), (x, 35))

    def _draw_hints(self):
        hint_y = self.SCREEN_H - 30
        hints = "TAB: Leaderboard   |   C: Controls   |   ESC: Menu"
        self.game.screen.blit(self.font_body.render(hints, True, (148, 163, 184)), (20, hint_y))
        if self.game.current_seed:
            lbl = self.font_mono.render(f"ID: {self.game.current_seed[:18]}...", True, (71, 85, 105))
            self.game.screen.blit(lbl, (self.SCREEN_W - lbl.get_width() - 20, hint_y))

    def _draw_overlay_bg(self):
        s = pygame.Surface((self.SCREEN_W, self.SCREEN_H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.game.screen.blit(s, (0, 0))

    def _draw_leaderboard_modal(self):
        w, h = 520, 440
        x, y = (self.SCREEN_W - w) // 2, (self.SCREEN_H - h) // 2
        pygame.draw.rect(self.game.screen, (30, 41, 59), (x, y, w, h), border_radius=12)
        pygame.draw.rect(self.game.screen, COL_ACCENT, (x, y, w, h), 2, border_radius=12)

        self.game.screen.blit(self.font_title.render("LEADERBOARD", True, COL_ACCENT), (x + 25, y + 20))
        self.game.screen.blit(self.font_body.render("[TAB] Close", True, (100, 100, 100)), (x + w - 110, y + 30))

        start_y = y + 80
        headers = ["#", "PLAYER", "SCORE", "TIME"]
        pxs = [x+25, x+70, x+320, x+420]
        for i, txt in enumerate(headers):
            self.game.screen.blit(self.font_hud_label.render(txt, True, (148, 163, 184)), (pxs[i], start_y))
        pygame.draw.line(self.game.screen, (71, 85, 105), (x+20, start_y+20), (x+w-20, start_y+20))
        
        row_y = start_y + 35
        if not self.cached_scores:
            lbl = self.font_body.render("No scores yet. Be the first!", True, (200, 200, 200))
            self.game.screen.blit(lbl, (x + w//2 - lbl.get_width()//2, row_y + 40))
        else:
            for i, s in enumerate(self.cached_scores[:8]):
                col = COL_TEXT
                if i == 0: col = COL_GOLD
                elif i == 1: col = (192, 192, 192)
                elif i == 2: col = (205, 127, 50)
                name = s['name'][:14] + ".." if len(s['name']) > 14 else s['name']
                self.game.screen.blit(self.font_body.render(str(i+1), True, col), (pxs[0], row_y))
                self.game.screen.blit(self.font_body.render(name, True, col), (pxs[1], row_y))
                self.game.screen.blit(self.font_body.render(f"{s['score']:.0f}", True, col), (pxs[2], row_y))
                self.game.screen.blit(self.font_body.render(f"{s['time']:.1f}s", True, col), (pxs[3], row_y))
                row_y += 32

        if self.finished:
            lbl = self.font_body.render("PRESS [R] TO RETRY   |   [T] NEW MAP", True, COL_SUCCESS)
            self.game.screen.blit(lbl, lbl.get_rect(center=(x+w//2, y+h-40)))

    def _draw_controls_modal(self):
        w, h = 420, 380
        x, y = (self.SCREEN_W - w) // 2, (self.SCREEN_H - h) // 2
        pygame.draw.rect(self.game.screen, (30, 41, 59), (x, y, w, h), border_radius=12)
        pygame.draw.rect(self.game.screen, (148, 163, 184), (x, y, w, h), 2, border_radius=12)
        self.game.screen.blit(self.font_title.render("CONTROLS", True, (148, 163, 184)), (x + 25, y + 20))
        
        controls = [("WASD / Arrows", "Move"), ("SHIFT + Move", "Break Wall"), ("ENTER", "Use Portal"), 
                    ("TAB", "Leaderboard"), ("B / H", "Toggle Hints"), ("R", "Retry"), ("T", "New Map"), ("ESC", "Menu")]
        cy = y + 80
        for key, desc in controls:
            self.game.screen.blit(self.font_mono.render(key, True, COL_ACCENT), (x + 30, cy))
            self.game.screen.blit(self.font_body.render(desc, True, COL_TEXT), (x + 200, cy))
            cy += 32
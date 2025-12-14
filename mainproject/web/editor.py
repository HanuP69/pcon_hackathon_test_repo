import pygame
import base64
import sys

import web.renderer as renderer
from web.renderer import _sprites

IS_WEB = sys.platform == "emscripten"
if IS_WEB:
    from platform import window

from web.state import GameState
from src.core.maze import Maze, CellType
from src.solver.bfs_solver import BFSSolver

CELL_SIZE = 32  
GRID_DIM = 15
PANEL_HEIGHT = 180 
PADDING = 20


COL_BG = (135, 206, 235)      
COL_PANEL_BG = (245, 245, 250)  
COL_ACCENT = (56, 126, 245)     
COL_BORDER = (180, 180, 190)
COL_HIGHLIGHT = (255, 215, 0)   
COL_TEXT = (50, 50, 60)
COL_SUBTEXT = (100, 100, 110)
COL_ERROR = (200, 50, 50)
COL_SUCCESS = (30, 150, 30)

TILE_EMPTY = "EMPTY"
TILE_WALL = "WALL"
TILE_START = "START"
TILE_GOAL = "GOAL"

class EditorScreen:
    def __init__(self, game):
        self.game = game
        
        # Fonts
        self.font_ui = pygame.font.SysFont("Segoe UI", 14)
        self.font_bold = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self.font_big = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_mono = pygame.font.SysFont("Consolas", 12)

        renderer.load_sprites()
        
        # Dimensions
        self.GRID_DIM = GRID_DIM
        self.grid_pixel_w = self.GRID_DIM * CELL_SIZE
        self.grid_pixel_h = self.GRID_DIM * CELL_SIZE
        
        screen_w, screen_h = self.game.screen.get_size()
        
        self.grid_origin_x = (screen_w - self.grid_pixel_w) // 2
        self.grid_origin_y = 20 
        
        panel_y = self.grid_origin_y + self.grid_pixel_h + 20
        self.panel_rect = pygame.Rect(
            (screen_w - 760) // 2, 
            panel_y, 
            760, 
            PANEL_HEIGHT
        )

        # UI State
        self.grid = [[TILE_EMPTY for _ in range(self.GRID_DIM)]
                     for _ in range(self.GRID_DIM)]
        
        self.selected = TILE_WALL
        self.selected_portal_id = None
        
        self.message = "Editor Ready."
        self.message_type = "neutral" 
        self.seed = None
        self.k_value = 3
        
        self.buttons = {} 

    def update(self):
        renderer.update_animation()

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1: 
                    self.handle_click(e.pos)

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.game.switch(GameState.MODE)
                elif e.key == pygame.K_p:
                    self.publish()
                elif e.key == pygame.K_UP:
                    self.change_k(1)
                elif e.key == pygame.K_DOWN:
                    self.change_k(-1)

    def change_k(self, delta):
        self.k_value = max(0, min(10, self.k_value + delta))

    def handle_click(self, pos):
        x, y = pos
        
        for key, rect in self.buttons.items():
            if rect.collidepoint(pos):
                self.handle_button_click(key)
                return

        gx = (x - self.grid_origin_x) // CELL_SIZE
        gy = (y - self.grid_origin_y) // CELL_SIZE
        
        if 0 <= gx < self.GRID_DIM and 0 <= gy < self.GRID_DIM:
            self.modify_grid(gx, gy)

    def handle_button_click(self, key):
        if isinstance(key, str) and key.startswith("TOOL_"):
            tool_name = key.replace("TOOL_", "")
            if tool_name in [TILE_EMPTY, TILE_WALL, TILE_START, TILE_GOAL]:
                self.selected = tool_name
                self.selected_portal_id = None
            elif tool_name.startswith("PORTAL_"):
                pid = int(tool_name.split("_")[1])
                self.selected = "PORTAL"
                self.selected_portal_id = pid
        
        elif key == "BTN_PLUS": self.change_k(1)
        elif key == "BTN_MINUS": self.change_k(-1)
        elif key == "BTN_PUBLISH": self.publish()

    def modify_grid(self, gx, gy):
        if self.selected in [TILE_START, TILE_GOAL]:
            self.clear_tile_type(self.selected)
        
        if self.selected == "PORTAL" and self.selected_portal_id is not None:
            if self.count_portal(self.selected_portal_id) >= 2:
                self.set_message(f"Portal {self.selected_portal_id} max (2)", "error")
                return
            self.grid[gx][gy] = ("PORTAL", self.selected_portal_id)
        else:
            self.grid[gx][gy] = self.selected
        
        self.set_message("Placed object.", "neutral")

    def clear_tile_type(self, tile_type):
        for i in range(self.GRID_DIM):
            for j in range(self.GRID_DIM):
                if self.grid[i][j] == tile_type:
                    self.grid[i][j] = TILE_EMPTY

    def count_portal(self, pid):
        count = 0
        for row in self.grid:
            for cell in row:
                if isinstance(cell, tuple) and cell[0] == "PORTAL" and cell[1] == pid:
                    count += 1
        return count
    
    def count_tile(self, t_type):
        return sum(1 for row in self.grid for cell in row if cell == t_type)

    def set_message(self, msg, m_type):
        self.message = msg
        self.message_type = m_type

    def publish(self):
        if self.count_tile(TILE_START) != 1:
            self.set_message("Error: Need exactly 1 Cat", "error")
            return
        if self.count_tile(TILE_GOAL) != 1:
            self.set_message("Error: Need exactly 1 Fish", "error")
            return
        
        for pid in range(6):
            c = self.count_portal(pid)
            if c != 0 and c != 2:
                self.set_message(f"Error: Portal {pid} needs 2 ends", "error")
                return

        maze = Maze(self.GRID_DIM, self.GRID_DIM)
        char_grid = []
        portal_map = {}

        for j in range(self.GRID_DIM):
            for i in range(self.GRID_DIM):
                cell_data = self.grid[i][j]
                cell = maze.grid[i][j]
                char = "."
                
                if cell_data == TILE_WALL:
                    cell.type = CellType.WALL
                    char = "#"
                elif cell_data == TILE_START:
                    cell.type = CellType.START
                    maze.start = (i, j)
                    char = "S"
                elif cell_data == TILE_GOAL:
                    cell.type = CellType.GOAL
                    maze.goal = (i, j)
                    char = "G"
                elif isinstance(cell_data, tuple):
                    pid = cell_data[1]
                    cell.type = CellType.PORTAL
                    cell.portal_id = pid
                    portal_map.setdefault(pid, []).append((i, j))
                    char = chr(ord('a') + pid)
                
                char_grid.append(char)
        
        for pid, coords in portal_map.items():
            maze.portals[pid] = tuple(coords)

        solver = BFSSolver(maze, self.k_value)
        if solver.shortest_path() == -1:
            self.set_message(f"Unsolvable with K={self.k_value}!", "error")
            return
        
        rle = []
        count = 1
        for k in range(1, len(char_grid)):
            if char_grid[k] == char_grid[k-1]:
                count += 1
            else:
                rle.append(f"{count}{char_grid[k-1]}")
                count = 1
        rle.append(f"{count}{char_grid[-1]}")
        
        payload = "".join(rle)
        encoded = base64.urlsafe_b64encode(payload.encode()).decode()
        self.seed = f"MS2|{self.GRID_DIM}x{self.GRID_DIM}|{self.k_value}|{encoded}"
        
        self.set_message("Seed Generated!", "success")
        
        if IS_WEB:
            try:
                window.prompt("Copy Seed:", self.seed)
            except:
                pass

    def _get_icon(self, key, size):
        s = _sprites.get(key)
        if s: return pygame.transform.scale(s, (size, size))
        return pygame.Surface((size, size))

    def draw(self):
        self.game.screen.fill(COL_BG)
        self.buttons = {} 

        grid_rect = pygame.Rect(self.grid_origin_x, self.grid_origin_y, self.grid_pixel_w, self.grid_pixel_h)
        pygame.draw.rect(self.game.screen, (0, 0, 0), grid_rect.move(2, 2)) # Shadow

        for i in range(self.GRID_DIM):
            for j in range(self.GRID_DIM):
                x = self.grid_origin_x + i * CELL_SIZE
                y = self.grid_origin_y + j * CELL_SIZE
                
                self.game.screen.blit(self._get_icon('grass', CELL_SIZE), (x, y))

                cell = self.grid[i][j]
                
                if cell == TILE_WALL:
                    self.game.screen.blit(self._get_icon('wall', CELL_SIZE), (x, y))
                elif cell == TILE_START:
                    self.game.screen.blit(self._get_icon('cat', CELL_SIZE), (x, y))
                elif cell == TILE_GOAL:
                    self.game.screen.blit(self._get_icon('fish', CELL_SIZE), (x, y))
                elif isinstance(cell, tuple):
                    p_img = renderer._generate_portal(cell[1], renderer._animation_frame)
                    p_img = pygame.transform.scale(p_img, (CELL_SIZE, CELL_SIZE))
                    self.game.screen.blit(p_img, (x, y))
                
                pygame.draw.rect(self.game.screen, (0, 0, 0, 20), (x, y, CELL_SIZE, CELL_SIZE), 1)

        px, py = self.panel_rect.topleft
        pw, ph = self.panel_rect.size
        
        pygame.draw.rect(self.game.screen, COL_PANEL_BG, self.panel_rect, border_radius=10)
        pygame.draw.rect(self.game.screen, COL_BORDER, self.panel_rect, 3, border_radius=10)

        def draw_btn(x, y, t_id, label=None, icon_key=None, surf=None):
            rect = pygame.Rect(x, y, 40, 40)
            self.buttons[t_id] = rect
            
            is_sel = False
            if "PORTAL" in t_id:
                pid = int(t_id.split("_")[2])
                if self.selected == "PORTAL" and self.selected_portal_id == pid: is_sel = True
            else:
                t_name = t_id.replace("TOOL_", "")
                if self.selected == t_name: is_sel = True
            
            bg = COL_HIGHLIGHT if is_sel else (255, 255, 255)
            if rect.collidepoint(pygame.mouse.get_pos()): bg = (240, 240, 240) if not is_sel else COL_HIGHLIGHT
            
            pygame.draw.rect(self.game.screen, bg, rect, border_radius=6)
            pygame.draw.rect(self.game.screen, COL_BORDER, rect, 1, border_radius=6)
            
            if surf:
                self.game.screen.blit(pygame.transform.scale(surf, (28,28)), (x+6, y+6))
            elif icon_key:
                self.game.screen.blit(self._get_icon(icon_key, 28), (x+6, y+6))
            
            if label:
                lbl = self.font_ui.render(label, True, COL_TEXT)
                self.game.screen.blit(lbl, (x + 2, y + 42))

        cx = px + 20
        cy = py + 20
        
        lbl = self.font_bold.render("TERRAIN", True, COL_SUBTEXT)
        self.game.screen.blit(lbl, (cx, cy))
        cy += 25
        
        draw_btn(cx, cy, f"TOOL_{TILE_WALL}", icon_key='wall')
        draw_btn(cx + 45, cy, f"TOOL_{TILE_EMPTY}", icon_key='grass')

        cx += 110
        cy = py + 20
        pygame.draw.line(self.game.screen, COL_BORDER, (cx-15, cy), (cx-15, py+ph-20))
        
        lbl = self.font_bold.render("PORTALS", True, COL_SUBTEXT)
        self.game.screen.blit(lbl, (cx, cy))
        cy += 25
        
        start_x = cx
        for pid in range(6):
            p_surf = renderer._generate_portal(pid, 0)
            draw_btn(cx, cy, f"TOOL_PORTAL_{pid}", surf=p_surf)
            cx += 45
            if pid == 2:
                cx = start_x
                cy += 45

        cx = start_x + 150
        cy = py + 20
        pygame.draw.line(self.game.screen, COL_BORDER, (cx-15, cy), (cx-15, py+ph-20))

        lbl = self.font_bold.render("ACTORS", True, COL_SUBTEXT)
        self.game.screen.blit(lbl, (cx, cy))
        cy += 25
        
        draw_btn(cx, cy, f"TOOL_{TILE_START}", icon_key='cat')
        draw_btn(cx + 45, cy, f"TOOL_{TILE_GOAL}", icon_key='fish')

        cx += 110
        cy = py + 20
        pygame.draw.line(self.game.screen, COL_BORDER, (cx-15, cy), (cx-15, py+ph-20))

        lbl = self.font_bold.render("BREAKS (K)", True, COL_SUBTEXT)
        self.game.screen.blit(lbl, (cx, cy))
        cy += 35
 
        m_rect = pygame.Rect(cx, cy, 30, 30)
        self.buttons["BTN_MINUS"] = m_rect
        pygame.draw.rect(self.game.screen, (230, 230, 235), m_rect, border_radius=4)
        m_txt = self.font_bold.render("-", True, COL_TEXT)
        self.game.screen.blit(m_txt, m_txt.get_rect(center=m_rect.center))
        
        v_rect = pygame.Rect(cx + 35, cy, 40, 30)
        pygame.draw.rect(self.game.screen, (255, 255, 255), v_rect, border_radius=4)
        v_txt = self.font_bold.render(str(self.k_value), True, COL_ACCENT)
        self.game.screen.blit(v_txt, v_txt.get_rect(center=v_rect.center))
        
        p_rect = pygame.Rect(cx + 80, cy, 30, 30)
        self.buttons["BTN_PLUS"] = p_rect
        pygame.draw.rect(self.game.screen, (230, 230, 235), p_rect, border_radius=4)
        p_txt = self.font_bold.render("+", True, COL_TEXT)
        self.game.screen.blit(p_txt, p_txt.get_rect(center=p_rect.center))

        cx += 140
        cy = py + 20
        pygame.draw.line(self.game.screen, COL_BORDER, (cx-15, cy), (cx-15, py+ph-20))
        
        btn_rect = pygame.Rect(cx, cy, 140, 40)
        self.buttons["BTN_PUBLISH"] = btn_rect
        
        col_btn = COL_ACCENT
        if btn_rect.collidepoint(pygame.mouse.get_pos()): col_btn = (70, 140, 255)
        pygame.draw.rect(self.game.screen, col_btn, btn_rect, border_radius=6)
        
        l_pub = self.font_bold.render("GENERATE", True, (255, 255, 255))
        self.game.screen.blit(l_pub, l_pub.get_rect(center=btn_rect.center))
        
        cy += 50
        msg_col = COL_TEXT
        if self.message_type == "error": msg_col = COL_ERROR
        elif self.message_type == "success": msg_col = COL_SUCCESS
        
        msg_surf = self.font_ui.render(self.message, True, msg_col)
        self.game.screen.blit(msg_surf, (cx, cy))
        
        if self.seed:
            s_surf = self.font_mono.render("Seed Copied!", True, (150, 150, 150))
            self.game.screen.blit(s_surf, (cx, cy + 20))
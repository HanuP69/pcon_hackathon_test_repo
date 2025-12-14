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
GRID_SIZE = 15
GRID_ORIGIN = (50, 50)

TILE_EMPTY = "EMPTY"
TILE_WALL = "WALL"
TILE_START = "START"
TILE_GOAL = "GOAL"

class EditorScreen:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Arial", 18)
        self.big_font = pygame.font.SysFont("Arial", 20, bold=True)

        renderer.load_sprites()
        

        self.GRID_DIM = 15  
        self.GRID_ORIGIN = (40, 40)
        
        self.grid_width = self.GRID_DIM * CELL_SIZE
        self.grid_height = self.GRID_DIM * CELL_SIZE
        
        self.palette_x = self.GRID_ORIGIN[0]+self.grid_width+40
        self.palette_y = self.GRID_ORIGIN[1]
        
        self.info_x = self.GRID_ORIGIN[0]
        self.info_y = self.GRID_ORIGIN[1]+self.grid_height+30
        
        self.grid = [[TILE_EMPTY for _ in range(self.GRID_DIM)]
                     for _ in range(self.GRID_DIM)]
        
        self.selected = TILE_WALL
        self.selected_portal_id = None
        self.message = ""
        self.seed = None
        self.k_value = 3

    def update(self):
        renderer.update_animation()

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
        

        px, py = self.palette_x, self.palette_y
        
        base_tiles = [TILE_EMPTY, TILE_WALL, TILE_START, TILE_GOAL]
        for tile in base_tiles:
            if pygame.Rect(px, py, 30, 30).collidepoint(pos):
                self.selected = tile
                self.selected_portal_id = None
                return
            py += 35
        
        py += 10
        for pid in range(6):
            if pygame.Rect(px, py, 30, 30).collidepoint(pos):
                self.selected = "PORTAL"
                self.selected_portal_id = pid
                return
            py += 35
        
        gx = (x-self.GRID_ORIGIN[0])//CELL_SIZE
        gy = (y-self.GRID_ORIGIN[1])//CELL_SIZE
        
        if not (0<=gx<self.GRID_DIM and 0 <=gy<self.GRID_DIM):
            return
        

        if self.selected in [TILE_START, TILE_GOAL]:
            self.clear_tile_type(self.selected)
        

        if self.selected == "PORTAL" and self.selected_portal_id is not None:
            if self.count_portal(self.selected_portal_id) >= 2:
                self.message = f"Portal {self.selected_portal_id} used max times"
                return
            self.grid[gx][gy] = ("PORTAL", self.selected_portal_id)
        else:
            self.grid[gx][gy] = self.selected

    def clear_tile_type(self, tile_type):
        for i in range(self.GRID_DIM):
            for j in range(self.GRID_DIM):
                if self.grid[i][j] == tile_type:
                    self.grid[i][j] = TILE_EMPTY

    def count_tile_type(self, tile_type):
        return sum(self.grid[i][j] == tile_type 
                   for i in range(self.GRID_DIM) for j in range(self.GRID_DIM))

    def count_portal(self, portal_id):
        count = 0
        for i in range(self.GRID_DIM):
            for j in range(self.GRID_DIM):
                cell = self.grid[i][j]
                if isinstance(cell, tuple) and cell[0] == "PORTAL" and cell[1] == portal_id:
                    count+=1 
        return count

    def publish(self):
        if self.count_tile_type(TILE_START) != 1 or self.count_tile_type(TILE_GOAL) != 1:
            self.message = "Error: Need exactly 1 Start (Cat) and 1 Goal (Fish)"
            return

        for pid in range(6):
            cnt = self.count_portal(pid)
            if cnt not in (0, 2):
                self.message = f"Error: Portal {pid} has {cnt} ends (needs 0 or 2)"
                return
        
        maze = Maze(self.GRID_DIM, self.GRID_DIM)
        portal_map = {}
        char_grid = []
        
        for j in range(self.GRID_DIM):
            for i in range(self.GRID_DIM):
                cell_data = self.grid[i][j]
                cell = maze.grid[i][j]
                char_code = "."
                
                if cell_data == TILE_WALL:
                    cell.type = CellType.WALL
                    char_code = "#"
                elif cell_data == TILE_EMPTY:
                    cell.type = CellType.EMPTY
                    char_code = "."
                elif cell_data == TILE_START:
                    cell.type = CellType.START
                    maze.start = (i, j)
                    char_code = "S"
                elif cell_data == TILE_GOAL:
                    cell.type = CellType.GOAL
                    maze.goal = (i, j)
                    char_code = "G"
                elif isinstance(cell_data, tuple) and cell_data[0] == "PORTAL":
                    pid = cell_data[1]
                    cell.type = CellType.PORTAL
                    cell.portal_id = pid
                    portal_map.setdefault(pid, []).append((i, j))
                    char_code = chr(ord('a') + pid)
                
                char_grid.append(char_code)
        
        for pid, cells in portal_map.items():
            maze.portals[pid] = (cells[0], cells[1])
        
        solver = BFSSolver(maze, self.k_value)
        if solver.shortest_path() == -1:
            self.message = f"Map is Unsolvable (even with K={self.k_value})!"
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
        self.seed = f"MS2|{self.GRID_DIM}x{self.GRID_DIM}|{self.k_value}|{encoded}"
        
        if IS_WEB:
            try:
                window.prompt("Copy this seed:", self.seed)
                self.message = "Seed copied to clipboard!"
            except:
                self.message = "Seed Generated (Check Console)"
        else:
             self.message = "Seed Generated!"

    def _get_scaled_sprite(self, key, size):
        sprite = _sprites.get(key)
        if sprite:
            return pygame.transform.scale(sprite, (size, size))
        return pygame.Surface((size, size))

    def draw(self):
        self.game.screen.fill((135, 206, 235))
        

        for i in range(self.GRID_DIM):
            for j in range(self.GRID_DIM):
                x = self.GRID_ORIGIN[0] + i * CELL_SIZE
                y = self.GRID_ORIGIN[1] + j * CELL_SIZE
                cell_data = self.grid[i][j]
                
                self.game.screen.blit(self._get_scaled_sprite('grass', CELL_SIZE), (x, y))
                
                if cell_data == TILE_WALL:
                    self.game.screen.blit(self._get_scaled_sprite('wall', CELL_SIZE), (x, y))
                elif cell_data == TILE_GOAL:
                    self.game.screen.blit(self._get_scaled_sprite('fish', CELL_SIZE), (x, y))
                elif cell_data == TILE_START:
                    self.game.screen.blit(self._get_scaled_sprite('cat', CELL_SIZE), (x, y))
                elif isinstance(cell_data, tuple) and cell_data[0] == "PORTAL":
                    portal_surf = renderer._generate_portal(cell_data[1], renderer._animation_frame)
                    scaled = pygame.transform.scale(portal_surf, (CELL_SIZE, CELL_SIZE))
                    self.game.screen.blit(scaled, (x, y))
                
                pygame.draw.rect(self.game.screen, (180, 180, 180), (x, y, CELL_SIZE, CELL_SIZE), 1)
        
        px, py = self.palette_x, self.palette_y
        
        panel_h = 440
        pygame.draw.rect(self.game.screen, (240, 240, 240), (px - 10, py - 10, 50, panel_h), border_radius=5)
        pygame.draw.rect(self.game.screen, (100, 149, 237), (px - 10, py - 10, 50, panel_h), 2, border_radius=5)
        
        ICON_SIZE = 30
        
        def draw_btn(sprite_key, is_selected, override_surf=None):
            if override_surf:
                img = pygame.transform.scale(override_surf, (ICON_SIZE, ICON_SIZE))
            else:
                img = self._get_scaled_sprite(sprite_key, ICON_SIZE)
            
            self.game.screen.blit(img, (px, py))
            if is_selected:
                pygame.draw.rect(self.game.screen, (255, 215, 0), (px-2, py-2, ICON_SIZE+4, ICON_SIZE+4), 3)
        
        draw_btn('grass', self.selected == TILE_EMPTY)
        py += 35
        draw_btn('wall', self.selected == TILE_WALL)
        py += 35
        draw_btn('cat', self.selected == TILE_START)
        py += 35
        draw_btn('fish', self.selected == TILE_GOAL)
        py += 35
        py += 10
        
        for pid in range(6):
            p_surf = renderer._generate_portal(pid, 0)
            is_sel = (self.selected == "PORTAL" and self.selected_portal_id == pid)
            draw_btn(None, is_sel, override_surf=p_surf)
            py += 35

        box_x = self.info_x
        box_y = self.info_y
        box_w = self.grid_width+80
        box_h = 160
        
  
        pygame.draw.rect(self.game.screen, (255, 255, 255), (box_x, box_y, box_w, box_h), border_radius=8)
        pygame.draw.rect(self.game.screen, (100, 149, 237), (box_x, box_y, box_w, box_h), 3, border_radius=8)
        
        title = self.big_font.render("Editor Controls", True, (100, 149, 237))
        self.game.screen.blit(title, (box_x + 15, box_y + 10))
        
        k_txt = self.font.render(f"Max Wall Breaks (K): {self.k_value}  (Use UP/DOWN arrows)", True, (50, 50, 50))
        self.game.screen.blit(k_txt, (box_x + 15, box_y + 40))
        
        help_txt = self.font.render("Left Click: Place   |   ESC: Menu   |   P: Publish & Generate Seed", True, (100, 100, 100))
        self.game.screen.blit(help_txt, (box_x + 15, box_y + 70))

        if self.message:
            color = (0, 150, 0)
            msg_surf = self.font.render(self.message, True, color)
            self.game.screen.blit(msg_surf, (box_x + 15, box_y + 100))

            if self.seed:
                seed_preview = self.font.render(f"Seed: {self.seed[:30]}...", True, (150, 150, 150))
                self.game.screen.blit(seed_preview, (box_x + 15, box_y + 125))
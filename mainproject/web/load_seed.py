import pygame
import base64
import re
import sys


IS_WEB = sys.platform == "emscripten"
if IS_WEB:
    from platform import window

from web.state import GameState
from src.core.maze import Maze, CellType

class SeedLoadScreen:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Arial", 26)
        self.seed_text = ""
        self.cursor_visible = True
        self.cursor_timer = 0
        self.message = ""

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.game.switch(GameState.MODE)
                    return
                elif e.key == pygame.K_RETURN:
                    self.try_load()
                    return
                elif e.key == pygame.K_BACKSPACE:
                    self.seed_text = self.seed_text[:-1]
                    return

                if e.key == pygame.K_v and (e.mod & pygame.KMOD_CTRL):
                    
                    if IS_WEB:
                        try:
                            text = window.prompt("Paste Seed Here:", "")
                            if text:
                                self.seed_text += text
                        except Exception as err:
                            print(f"ERROR: {err}")
                    else:
                        try:
                            import tkinter
                            tk = tkinter.Tk()
                            tk.withdraw()
                            self.seed_text += tk.clipboard_get()
                            tk.destroy()
                        except:
                            print("Clipboard not available")
                    return

                if e.unicode.isprintable() and not (e.mod & pygame.KMOD_CTRL):
                    self.seed_text += e.unicode

    def rle_decode(self, s):
        result = []
        for count, char in re.findall(r"(\d+)(.)", s):
            result.extend(char * int(count))
        return result

    def try_load(self):
        self.message = "Loading..."
        try:
            raw = self.seed_text.strip()
            if not raw: return
            parts = raw.split("|")

            version = parts[0]
            k_val = 0
            
            if version == "MS2":
                if len(parts) != 4: raise ValueError("Invalid MS2 format")
                size_str = parts[1]
                k_val = int(parts[2])
                payload = parts[3]
            elif version == "MS1":
                if len(parts) != 3: raise ValueError("Invalid MS1 format")
                size_str = parts[1]
                k_val = 3
                payload = parts[2]
            else:
                raise ValueError("Unknown Version")

            W, H = map(int, size_str.split("x"))
            pad = len(payload) % 4
            if pad: payload += '=' * (4 - pad)
            decoded = base64.urlsafe_b64decode(payload).decode()
            flat = self.rle_decode(decoded)
            
            if len(flat) != W * H:
                raise ValueError(f"Size mismatch: {len(flat)} vs {W*H}")

            maze = Maze(W, H)
            portal_map = {}
            idx = 0
            for j in range(H):
                for i in range(W):
                    ch = flat[idx]
                    idx += 1
                    cell = maze.grid[j][i] 
                    if ch == "#": cell.type = CellType.WALL
                    elif ch == ".": cell.type = CellType.EMPTY
                    elif ch == "S": 
                        cell.type = CellType.START
                        maze.start = (j, i)
                    elif ch == "G": 
                        cell.type = CellType.GOAL
                        maze.goal = (j, i)
                    elif "a" <= ch <= "j":
                        pid = ord(ch) - ord("a")
                        cell.type = CellType.PORTAL
                        cell.portal_id = pid
                        portal_map.setdefault(pid, []).append((j, i))

            for pid, pts in portal_map.items():
                if len(pts) == 2: maze.portals[pid] = (pts[0], pts[1])

            self.game.switch(GameState.PLAY, custom_maze=maze, fixed_k=k_val)

        except Exception as e:
            print(f"Load Error: {e}")
            self.message = "Invalid Seed"

    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer > 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self):
        self.game.screen.fill((20, 20, 20))
        t = self.font.render("Paste Seed (Ctrl+V):", True, (255, 255, 255))
        self.game.screen.blit(t, (150, 200))

        pygame.draw.rect(self.game.screen, (255, 255, 255), (120, 250, 560, 40), 2)
        disp = self.seed_text[-50:]
        txt = self.font.render(disp + ("|" if self.cursor_visible else ""), True, (255, 255, 0))
        self.game.screen.blit(txt, (130, 258))

        if self.message:
            m = self.font.render(self.message, True, (255, 100, 100))
            self.game.screen.blit(m, (150, 310))

        h = self.font.render("ENTER to Load, ESC to Return", True, (150, 150, 150))
        self.game.screen.blit(h, (150, 360))
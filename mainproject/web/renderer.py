import pygame
import math
import os
from src.core.maze import CellType

CELL = 32

_sprites = {}
_animation_frame = 0

def get_asset_path(filename):

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    return os.path.join(project_root, 'assets', filename)

def load_sprites():

    assets = {
        'grass': 'grass.png',
        'wall':  'wall.png',
        'cat':   'cat.png',
        'fish':  'fish.png'
    }

    for key, filename in assets.items():
        path = get_asset_path(filename)
        try:
            image = pygame.image.load(path).convert_alpha()

            _sprites[key] = pygame.transform.scale(image, (CELL, CELL))
        except (FileNotFoundError, pygame.error) as e:
            #don't do no shit

            fallback = pygame.Surface((CELL, CELL))
            if key == 'grass': fallback.fill((34, 139, 34))
            elif key == 'wall': fallback.fill((70, 70, 70))
            elif key == 'cat': fallback.fill((255, 165, 0))
            elif key == 'fish': fallback.fill((0, 0, 255))
            _sprites[key] = fallback



PORTAL_COLORS = [
    (255, 0, 255),    
    (0, 255, 255),
    (255, 255, 0),    
    (255, 128, 0),    
    (128, 0, 255),    
    (0, 255, 128),   
]

def _generate_portal(portal_id, frame):

    portal = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    color = PORTAL_COLORS[portal_id % len(PORTAL_COLORS)]
    center = CELL // 2
    

    pulse = math.sin(frame * 0.1) * 0.2 + 0.8
    radius = int((CELL // 2 - 2) * pulse)
    

    for i in range(3):
        glow_radius = radius + (3 - i) * 2
        pygame.draw.circle(portal, (*color, 50), (center, center), glow_radius)
    

    pygame.draw.circle(portal, color, (center, center), radius)
    

    inner_color = tuple(min(255, c + 50) for c in color)
    inner_radius = int(radius * 0.6)
    pygame.draw.circle(portal, inner_color, (center, center), inner_radius)
    

    font = pygame.font.SysFont("Arial", CELL // 2, bold=True)
    text = font.render(str(portal_id), True, (255, 255, 255))
    text_rect = text.get_rect(center=(center, center))
    portal.blit(text, text_rect)
    
    return portal

def get_portal_color(pid):

    return PORTAL_COLORS[pid % len(PORTAL_COLORS)]

def update_animation():

    global _animation_frame
    _animation_frame += 1
    if _animation_frame > 1000:
        _animation_frame = 0



def draw_maze(screen, maze, font):

    global _animation_frame
    

    if not _sprites:
        load_sprites()
    
    for i in range(maze.rows):
        for j in range(maze.cols):
            cell = maze.grid[i][j]
            x = j * CELL
            y = i * CELL
            

            screen.blit(_sprites['grass'], (x, y))
            

            if cell.type == CellType.WALL:
                screen.blit(_sprites['wall'], (x, y))
            
            elif cell.type == CellType.PORTAL:
                portal_tile = _generate_portal(cell.portal_id, _animation_frame)
                screen.blit(portal_tile, (x, y))
            
            elif cell.type == CellType.GOAL:
                screen.blit(_sprites['fish'], (x, y))

def draw_player(screen, player):

    global _animation_frame
    
    if not _sprites:
        load_sprites()

    x = player.y * CELL
    y = player.x * CELL
    

    bounce = abs(math.sin(_animation_frame*0.2))*2
    
    screen.blit(_sprites['cat'], (x, int(y-bounce)))

def draw_path(screen, path, color=(255, 215, 0)):

    if not path or len(path)<2:
        return
    

    points = []
    for x, y in path:
        px = y*CELL+CELL//2
        py = x*CELL+CELL//2
        points.append((px, py))
    

    if len(points)>=2:
        pygame.draw.lines(screen, color, False, points, 3)
    

    for point in points:
        pygame.draw.circle(screen, color, point, 4)
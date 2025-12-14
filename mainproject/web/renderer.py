import pygame
from src.core.maze import CellType

CELL = 20

BASE_COLORS = {
    CellType.WALL: (0, 0, 0),
    CellType.EMPTY: (255, 255, 255),
    CellType.START: (0, 200, 0),
    CellType.GOAL: (200, 0, 0),
}

PORTAL_COLORS = [
    (0, 120, 255),    
    (255, 80, 80),    
    (160, 80, 255),   
    (255, 160, 0),    
    (0, 180, 120),    
    (200, 200, 0)   
]


def get_portal_color(pid):
    return PORTAL_COLORS[pid % len(PORTAL_COLORS)]


def draw_maze(screen, maze, font):
    for i in range(maze.rows):
        for j in range(maze.cols):
            cell = maze.grid[i][j]

            if cell.type == CellType.PORTAL:
                color = get_portal_color(cell.portal_id)
            else:
                color = BASE_COLORS.get(cell.type, (255, 255, 255))

            rect = pygame.Rect(j * CELL, i * CELL, CELL, CELL)
            pygame.draw.rect(screen, color, rect)

            if cell.type == CellType.START:
                txt = font.render("S", True, (0, 0, 0))
                screen.blit(txt, txt.get_rect(center=rect.center))

            elif cell.type == CellType.GOAL:
                txt = font.render("G", True, (0, 0, 0))
                screen.blit(txt, txt.get_rect(center=rect.center))

def draw_player(screen, player):
    pygame.draw.circle(
        screen,
        (255, 255, 0),
        (player.y*CELL+CELL//2,
         player.x *CELL+CELL//2),
        CELL//3
    )
def draw_path(screen, path, color=(255, 215, 0)):
    if not path:
        return

    CELL = 20
    for x, y in path:
        rect = pygame.Rect(y*CELL+4, x * CELL+4, CELL-8, CELL-8)
        pygame.draw.rect(screen, color, rect)



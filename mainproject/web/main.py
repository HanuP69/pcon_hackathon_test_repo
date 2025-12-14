import asyncio
import random
import time
import pygame
from web.game import Game

async def main():
    random.seed(int(time.time() * 1000))

    pygame.init()
    screen = pygame.display.set_mode((800, 800))
    pygame.display.set_caption("Maze Solver")

    clock = pygame.time.Clock()
    game = Game(screen)

    while True:
        game.handle_events()
        game.update()
        game.draw()
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

asyncio.run(main())

import asyncio
import pygame
from web.main import Game 

async def main():
    pygame.init()
    
    game = Game()
    
    while True:

        game.current_screen.handle_events() 

        game.current_screen.update()
        game.current_screen.draw()
        pygame.display.update()
        
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())
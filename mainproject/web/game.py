import pygame
import os
from web.editor import EditorScreen
from web.load_seed import SeedLoadScreen
from web.state import GameState
from web.screens import WelcomeScreen, NameScreen, ModeScreen, PlayScreen

class Game:
    def __init__(self, screen):
        
        self.screen = screen
        self.state = GameState.WELCOME
        self.player_name = ""
        self.mode = None  


        self.current_music = None

        self.screens = {
            GameState.WELCOME: WelcomeScreen(self),
            GameState.NAME: NameScreen(self),
            GameState.MODE: ModeScreen(self),
        }

        self.current = self.screens[self.state]
        
        self.update_music()

    def update_music(self):

        target_music = None
        

        if self.state in [GameState.WELCOME, GameState.NAME, GameState.MODE, GameState.LOAD]:
            target_music = "menu.ogg"
        elif self.state == GameState.PLAY:
            target_music = "play.ogg"
        elif self.state == GameState.EDITOR:
            target_music = "editor.ogg"


        if target_music and target_music != self.current_music:
            path = os.path.join("assets", target_music)
            if os.path.exists(path):
                try:
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(0.4) 
                    pygame.mixer.music.play(-1)        
                    self.current_music = target_music
                except Exception as e:pass
                     
            
               

    def switch(self, new_state, **kwargs):
        self.state = new_state

        if new_state == GameState.PLAY:
            self.current = PlayScreen(self, **kwargs)

        elif new_state == GameState.EDITOR:
            self.current = EditorScreen(self)

        elif new_state == GameState.LOAD:
            self.current = SeedLoadScreen(self)

        else:
            self.current = self.screens[new_state]

        self.update_music()

    def handle_events(self):
        self.current.handle_events()

    def update(self):
        self.current.update()

    def draw(self):
        self.current.draw()
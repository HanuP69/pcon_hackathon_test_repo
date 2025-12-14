import pygame
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

        self.screens = {
            GameState.WELCOME: WelcomeScreen(self),
            GameState.NAME: NameScreen(self),
            GameState.MODE: ModeScreen(self),
        }

        self.current = self.screens[self.state]

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


    def handle_events(self):
        self.current.handle_events()

    def update(self):
        self.current.update()

    def draw(self):
        self.current.draw()

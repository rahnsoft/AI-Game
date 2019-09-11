import pygame
from collections import defaultdict
from app.resources.event_handler import SET_GAME_STATE
from app.resources import colours
from app.resources import text_renderer
from app.view import animations
from app.resources.music import MusicManager
from app.view.menu import Menu, MenuItem, SettingsMenu, ButtonMenuItem, TeamViewer

class TitleBanner:
    def __init__(self, text):
        words = text.split()
        word_surfaces = []
        max_height = 0
        max_width  = 0

        for word in words:
            ws = text_renderer.render_title(word, colours.COLOUR_WHITE)
            if ws.get_height() > max_height:
                max_height = ws.get_height()
            if ws.get_width() > max_width:
                max_width = ws.get_width()
            word_surfaces.append(ws)

        self.surface = pygame.Surface((max_width, max_height*len(words)))

        for i in range(len(word_surfaces)):
            y = i*max_height
            x = (max_width - word_surfaces[i].get_width())//2
            self.surface.blit(word_surfaces[i], (x,y))

    def render(self):
        return self.surface

class State:
    def render(self):
        return
    def update(self, delta_t):
        return
    def handle_event(self, event):
        return
    def exit_state(self):
        return

class StateTeamView(State):
    def __init__(self, main_menu):
        self.parent     = main_menu.parent
        self.main_menu  = main_menu
        self.teams      = self.parent.teams

        self.parent.event_handler.register_key_listener(self.handle_keypress)
        self.title = text_renderer.render_title("Teams", colours.COLOUR_WHITE)
        self.title_position = (
            (self.parent.resolution[0] - self.title.get_width())// 2,
            15
        )

        self.directions = {
            pygame.K_RIGHT     : [1],
            pygame.K_LEFT      : [-1],
            pygame.K_ESCAPE    : [3],
            pygame.K_BACKSPACE : [3]
        }

        self.animation = None

        menu_region = (self.parent.resolution[0],
            600
        )
        self.menu = TeamViewer(menu_region, self.teams)
        self.menu.register_finished_callback(self.finished)

    def render(self):
        surface = pygame.Surface(self.parent.resolution)
        surface.blit(self.title, self.title_position)
        surface.blit(self.menu.render(), (0,(15 + self.title.get_height() + self.parent.resolution[1]-self.menu.height)//2))
        return surface

    def handle_keypress(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in self.directions:
                magnitude = self.directions[event.key]
                self.animation = animations.Timeout(
                    self.menu.move_selection,
                    [magnitude[0]]
                )
        else:
            if event.key in self.directions:
                self.animation = None

    def finished(self):
        self.main_menu.set_state('default')

    def update(self, delta_t):
        if self.animation != None:
            self.animation.animate(delta_t)

    def exit_state(self):
        self.parent.event_handler.unregister_key_listener(self.handle_keypress)

class StateSettings(State):
    def __init__(self, main_menu):
        self.parent     = main_menu.parent
        self.main_menu  = main_menu
        self.settings   = self.parent.settings

        self.parent.event_handler.register_key_listener(self.handle_keypress)
        self.title = text_renderer.render_title("Options", colours.COLOUR_WHITE)

        self.title_position = (
            (self.parent.resolution[0] - self.title.get_width())// 2,
            15
        )

        self.directions = {
            pygame.K_UP        : [-1,  0],
            pygame.K_DOWN      : [ 1,  0],
            pygame.K_RIGHT     : [ 0,  1],
            pygame.K_LEFT      : [ 0, -1],
            pygame.K_SPACE     : [ 0,  2],
            pygame.K_RETURN    : [ 0,  2],
            pygame.K_ESCAPE    : [ 0,  3],
            pygame.K_BACKSPACE : [ 0,  3]
        }
        self.animation = None
        self.menu = SettingsMenu(self.settings)

        self.menu.register_finished_callback(self.finished)

    def render(self):
        surface = pygame.Surface(self.parent.resolution)
        surface.blit(self.title, self.title_position)
        m_surface = self.menu.render()
        surface.blit(m_surface, (
                (self.parent.resolution[0]-m_surface.get_width())//2,
                max(130, (self.parent.resolution[1]-m_surface.get_height())//2)
            )
        )
        return surface

    def handle_keypress(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in self.directions:
                magnitude = self.directions[event.key]
                if magnitude[0] != 0:
                    self.animation = animations.Timeout(
                        self.menu.move_selection,
                        [magnitude[0]]
                    )
                elif magnitude[1] != 0:
                    self.animation = animations.Timeout(
                        self.menu.click_selected,
                        [magnitude[1]]
                    )
        else:
            if event.key in self.directions:
                self.animation = None

    def finished(self):
        self.main_menu.set_state('default')

    def update(self, delta_t):
        if self.animation != None:
            self.animation.animate(delta_t)

    def exit_state(self):
        self.parent.event_handler.unregister_key_listener(self.handle_keypress)

class StateAnimatedIntro(State):
    def __init__(self, main_menu):
        self.parent     = main_menu.parent
        self.main_menu  = main_menu
        self.title_banner = main_menu.title_banner
        self.alpha = 0

        self.animation  = 0

        self.animations = [
            animations.FadeIn(self.set_alpha),
        ]

        self.parent.event_handler.register_key_listener(self.handle_keypress)

    def set_alpha(self, alpha):
        self.alpha = alpha

    def render(self):
        surface = pygame.Surface(self.parent.resolution)
        surface.blit(self.title_banner.render(), self.main_menu.banner_position)
        surface.blit(self.main_menu.menu.get_menu_surface(), self.main_menu.menu_position)

        mask = pygame.Surface(self.parent.resolution, pygame.SRCALPHA)
        mask.fill((0,0,0, 255-self.alpha))
        surface.blit(mask, (0,0))

        return surface

    def update(self, delta_t):
        if self.animations[self.animation].finished():
            self.animation += 1

        if self.animation == len(self.animations):
            self.main_menu.set_state('default')
        else:
            self.animations[self.animation].animate(delta_t)

    def skip(self):
        for animation in range(self.animation, len(self.animations)):
            self.animations[animation].skip()

    def handle_keypress(self, event):
        if event.type == pygame.KEYDOWN:
            self.main_menu.set_state('default')

    def exit_state(self):
        self.skip()
        self.parent.event_handler.unregister_key_listener(self.handle_keypress)

class StateAnimatedOutro(State):
    def __init__(self, main_menu):
        self.parent     = main_menu.parent
        self.main_menu  = main_menu
        self.title_banner = main_menu.title_banner
        self.alpha = 255

        self.music_manager = MusicManager()
        self.volume = self.music_manager.get_music_volume()

        fade = animations.ParallelAnimation()
        fade_display = animations.FadeOut(self.set_alpha, time=3000)
        fade_sound = animations.MoveValue(self.music_manager.set_music_volume, self.volume, 0,  time=3000)
        fade.add_animation(fade_display)
        fade.add_animation(fade_sound)
        self.animations = fade

        self.parent.event_handler.register_key_listener(self.handle_keypress)

    def set_alpha(self, alpha):
        self.alpha = alpha

    def render(self):
        surface = pygame.Surface(self.parent.resolution)
        surface.blit(self.title_banner.render(), self.main_menu.banner_position)
        surface.blit(self.main_menu.menu.get_menu_surface(), self.main_menu.menu_position)

        mask = pygame.Surface(self.parent.resolution, pygame.SRCALPHA)
        mask.fill((0,0,0, 255-self.alpha))
        surface.blit(mask, (0,0))

        return surface

    def update(self, delta_t):
        if self.animations.finished():
            self.exit_state()
        else:
            self.animations.animate(delta_t)

    def skip(self):
        self.animations.skip()

    def handle_keypress(self, event):
        if event.type == pygame.KEYDOWN:
            self.skip()

    def exit_state(self):
        self.parent.event_handler.unregister_key_listener(self.handle_keypress)
        event = pygame.event.Event(SET_GAME_STATE, state="in_game", seed='league_view')
        pygame.event.post(event)

class StateDefault(State):
    def __init__(self, main_menu):
        self.parent     = main_menu.parent
        self.main_menu  = main_menu
        self.title_banner = main_menu.title_banner
        self.parent.event_handler.register_key_listener(self.handle_keypress)
        self.main_menu.menu.selected = 0
        self.animation = None

        self.directions = {
            pygame.K_UP   : -1,
            pygame.K_DOWN : 1
        }

    def render(self):
        surface = pygame.Surface(self.parent.resolution)
        surface.blit(self.title_banner.render(), self.main_menu.banner_position)
        surface.blit(self.main_menu.menu.render(), self.main_menu.menu_position)
        return surface

    def handle_keypress(self, event):

        if event.type == pygame.KEYDOWN:
            if event.key in self.directions:
                self.animation = animations.Timeout(
                    self.main_menu.menu.move_selection,
                    [self.directions[event.key]]
                )
            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                self.main_menu.menu.click_selected()
        else:
            if event.key in self.directions:
                self.animation = None

    def update(self, delta_t):
        if self.animation != None:
            self.animation.animate(delta_t)

    def exit_state(self):
        self.parent.event_handler.unregister_key_listener(self.handle_keypress)

class MainMenu:
    def __init__(self, parent, state_seed='default'):
        self.parent = parent
        self.event_handler = parent.event_handler
        self.title_banner = TitleBanner(self.parent.title)
        self.banner_position = (self.parent.resolution[0]//10, self.parent.resolution[1]//10)

        self.menu = Menu([
            ButtonMenuItem("Start", self.start_game),
            ButtonMenuItem("View Teams", self.show_teams),
            ButtonMenuItem("Options", self.show_settings),
            ButtonMenuItem("Exit", self.trigger_exit)]
        )

        self.states = {
            "intro"     : StateAnimatedIntro,
            "settings"  : StateSettings,
            "default"   : StateDefault,
            "team_view" : StateTeamView,
            "outro"     : StateAnimatedOutro,
        }
        self.compute_widget_positions()

        self.state_code = state_seed
        self.state = self.states[self.state_code](self)

    def set_state(self, state):
        self.state.exit_state()
        self.state_code = state
        self.state = self.states[state](self)

    def update_display(self):
        self.compute_widget_positions()

    def compute_widget_positions(self):
        self.menu_position = (
            self.parent.resolution[0]-self.parent.resolution[0]//10-self.menu.surface.get_width(),
            self.parent.resolution[1]-self.parent.resolution[1]//5-self.menu.surface.get_height()
        )

    def render(self):
        return self.state.render()

    def update(self, delta_t):
        return self.state.update(delta_t)

    def handle_event(self, event):
        return self.state.handle_event()

    def show_settings(self):
        self.set_state('settings')

    def show_teams(self):
        self.set_state('team_view')

    def start_game(self):
        self.set_state('outro')

    def trigger_exit(self):
        event = pygame.event.Event(pygame.QUIT)
        pygame.event.post(event)

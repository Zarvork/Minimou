import pygame
import pygame_gui

class ChallengeWindow(pygame_gui.elements.UIWindow):
    """Window containing the three challenge difficulty buttons."""

    def __init__(
        self,
        rect,
        manager,
        on_easy,
        on_medium,
        on_hard
    ):
        super().__init__(
            rect,
            manager=manager,
            window_display_title="Challenge",
            resizable=False,
            draggable=True
        )

        self.on_easy = on_easy
        self.on_medium = on_medium
        self.on_hard = on_hard

        container = self.get_container()

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                30,
                30,
                rect.width - 60,
                50
            ),
            text="Choose a difficulty:",
            manager=manager,
            container=container
        )

        self.easy_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                30,
                90,
                rect.width - 60,
                55
            ),
            text="EASY",
            manager=manager,
            container=container
        )

        self.medium_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                30,
                160,
                rect.width - 60,
                55
            ),
            text="MEDIUM",
            manager=manager,
            container=container
        )

        self.hard_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                30,
                230,
                rect.width - 60,
                55
            ),
            text="HARD",
            manager=manager,
            container=container
        )

    def process_event(self, event):

        if event.type == pygame_gui.UI_BUTTON_PRESSED:

            if event.ui_element == self.easy_button:
                self.on_easy()
                self.kill()
                return True

            if event.ui_element == self.medium_button:
                self.on_medium()
                self.kill()
                return True

            if event.ui_element == self.hard_button:
                self.on_hard()
                self.kill()
                return True

        return super().process_event(event)

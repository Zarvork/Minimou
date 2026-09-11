import pygame
import pygame_gui


class ClearConfirmationWindow(pygame_gui.elements.UIWindow):
    """Confirmation window shown before clearing the canvas."""

    def __init__(self, rect, manager, on_confirm, on_close):
        super().__init__(
            rect,
            manager=manager,
            window_display_title="Confirm Clear",
            resizable=False,
            draggable=True,
        )

        self.on_confirm = on_confirm
        self.on_close = on_close

        container = self.get_container()

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(30, 30, rect.width - 60, 70),
            text="Are you sure you want to clear the canvas?",
            manager=manager,
            container=container,
        )

        self.confirm_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(30, 120, rect.width - 60, 55),
            text="CLEAR",
            manager=manager,
            container=container,
        )

        self.cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(30, 190, rect.width - 60, 55),
            text="CANCEL",
            manager=manager,
            container=container,
        )

    def process_event(self, event):

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.confirm_button:
                self.on_confirm()
                self.on_close()
                self.kill()
                return True

            if event.ui_element == self.cancel_button:
                self.on_close()
                self.kill()
                return True

        return super().process_event(event)

import pygame
import pygame_gui


class EmailWindow(pygame_gui.elements.UIWindow):
    def __init__(self, rect, manager, on_send, on_close):
        super().__init__(
            rect,
            manager=manager,
            window_display_title="Send painting",
            resizable=False,
            draggable=True,
        )

        self.on_send = on_send
        self.on_close = on_close

        container = self.get_container()

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(20, 20, 360, 35),
            text="Recipient email:",
            manager=manager,
            container=container,
        )

        self.email_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(20, 65, 360, 40),
            manager=manager,
            container=container,
        )

        self.send_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(20, 120, 170, 45),
            text="Send",
            manager=manager,
            container=container,
        )

        self.cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(210, 120, 170, 45),
            text="Cancel",
            manager=manager,
            container=container,
        )

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.send_button:
                self.on_send(self.email_entry.get_text())
                self.on_close()
                self.kill()
                return True

            if event.ui_element == self.cancel_button:
                self.on_close()
                self.kill()
                return True

        return super().process_event(event)

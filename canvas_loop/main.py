import pygame
import pygame_gui
import pygame.mouse
import pygame_widgets
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from pygame_gui.elements import UIButton

BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50

colors = [
    "#ff0000",
    "#00ff00",
    "#0000ff",
    "#ffff00",
    "#ff00ff",
    "#00ffff",
    "#f5f5f5",
    "#a7661d",
    "#000000",
]

object_ids = [
    "#red_button",
    "#green_button",
    "#blue_button",
    "#yellow_button",
    "#magenta_button",
    "#cyan_button",
    "#grey_button",
    "#pink_button",
    "#black_button",
]

    # clear_pos = pygame.Vector2(width * 49 / 50, height / 20)
def main():
    pygame.init()

    drawing_color = "#000000"
    running = True
    dt = 0
    last_pos = None

    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((1280, 720))
    width, height = screen.get_width(), screen.get_height()
    remaining_height = height - BUTTON_HEIGHT

    screen.fill(pygame.Color('#ffffff'))

    canvas = pygame.Surface((width, height))   # <- dedicated painting layer
    canvas.fill("#ffffff")

    slider = Slider(screen, 10, 10, 200, 40, min=0, max=99, step=1,
                     colour=(210, 210, 210), handleColour=(120, 120, 120),
                     valueColour=(210, 210, 210), borderColour=(150, 150, 150),
                     borderThickness=1, initial=10)
    output = TextBox(screen, 240, 10, 40, 40, fontSize=20)
    output.disable()

    slider_rect = pygame.Rect(10, 10, 200, 40)
    output_rect = pygame.Rect(240, 10, 40, 40)
    ui_panel_rect = pygame.Rect(width - BUTTON_WIDTH, 0, BUTTON_WIDTH, height)

    def is_over_ui(pos):
        return (slider_rect.collidepoint(pos)
                or output_rect.collidepoint(pos)
                or ui_panel_rect.collidepoint(pos))

    manager = pygame_gui.UIManager((1280, 720), theme_path="theme.json")

    clear_button_layout = pygame.Rect(
        (width - BUTTON_WIDTH,
        0),
        (BUTTON_WIDTH,
        BUTTON_HEIGHT)
    )
    clear_button = UIButton(
        relative_rect=clear_button_layout,
        text='Clear',
        manager=manager
    )
    color_buttons = []
    for i in range(9):
        color_i_layout = pygame.Rect(
            (width - BUTTON_WIDTH,
            BUTTON_HEIGHT + i * remaining_height / 10),
            (BUTTON_WIDTH,
            remaining_height / 10)
        )
        color_buttons.append(
            UIButton(
                relative_rect=color_i_layout,
                text='',
                manager=manager,
                object_id=object_ids[i]
            )
        )
    
    raw_eraser = pygame.image.load('eraser.png').convert_alpha()
    icon_size = (BUTTON_WIDTH - 20, remaining_height / 10 - 20)
    eraser_icon = pygame.transform.smoothscale(raw_eraser, icon_size)

    brush_button_layout = pygame.Rect(
        (width - BUTTON_WIDTH,
        BUTTON_HEIGHT + 9 * remaining_height / 10),
        (BUTTON_WIDTH,
        remaining_height / 10)
    )
    brush_button = UIButton(
        relative_rect=brush_button_layout,
        text='',
        manager=manager,
    )
    brush_button.set_image(eraser_icon)

    is_drawing = False
    while running:
        drawing_size = slider.getValue()

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if not is_over_ui(event.pos):
                    is_drawing = True
                    last_pos = event.pos

            if event.type == pygame.MOUSEBUTTONUP:
                is_drawing = False
                last_pos = None

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == clear_button:
                    canvas.fill("#ffffff")          # <- clear the canvas, not screen
                if event.ui_element == brush_button:
                    drawing_color = "#ffffff"
                for i, button in enumerate(color_buttons):
                    if event.ui_element == button:
                        drawing_color = colors[i]

            manager.process_events(event)

        if is_drawing:
            current_pos = pygame.mouse.get_pos()
            if not is_over_ui(current_pos):
                if last_pos is not None and not is_over_ui(last_pos):
                    distance = pygame.Vector2(current_pos).distance_to(last_pos)
                    step = max(drawing_size / 4, 1)
                    steps = max(int(distance / step), 1)
                    for i in range(steps + 1):
                        t = i / steps
                        interp_x = last_pos[0] + (current_pos[0] - last_pos[0]) * t
                        interp_y = last_pos[1] + (current_pos[1] - last_pos[1]) * t
                        pygame.draw.circle(canvas, drawing_color, (int(interp_x), int(interp_y)), drawing_size)
            last_pos = current_pos

        screen.blit(canvas, (0, 0))   # <- redraw the canvas fresh, every frame, first

        manager.update(dt)
        manager.draw_ui(screen)
        output.setText(slider.getValue())

        pygame_widgets.update(events)
        pygame.display.flip()
        dt = clock.tick(60) / 1000

    pygame.quit()


if __name__ == "__main__":
    main()

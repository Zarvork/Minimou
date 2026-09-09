import threading

import time
import image_subscriber
import pygame
import pygame_gui
import pygame_widgets
from challenge import ChallengeWindow
from clearwindow import ClearConfirmationWindow
from pygame_gui.elements import UIButton, UITextBox
from colorpicker import RadialColorPickerWindow
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox

BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
MAX_HISTORY = 20


def push_canvas_state(states, index, canvas):
    """Add a new canvas state and remove any redo states."""

    del states[index + 1 :]
    states.append(canvas.copy())

    if len(states) > MAX_HISTORY:
        states.pop(0)
        index -= 1

    return index + 1


def main():
    # ================================================
    #          Initialize Pygame variables
    # ================================================

    pygame.init()
    threading.Thread(target=image_subscriber.receive_image, daemon=True).start()

    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((1280, 720))
    width, height = screen.get_size()

    selected_color = pygame.Color("#000000")
    drawing_color = pygame.Color(selected_color)

    canvas = pygame.Surface((width, height))
    canvas.fill(pygame.Color("#ffffff"))

    raw_baptiste = pygame.image.load("baptiste.jpg").convert()
    raw_eraser = pygame.image.load("eraser.png").convert_alpha()
    eraser_icon = pygame.transform.smoothscale(raw_eraser, (BUTTON_WIDTH - 20, 40))

    # ================================================
    #            Define Python variables
    # ================================================

    nb_buffered_time = 0.5
    previous_point = None
    canvas_states = [canvas.copy()]
    current_state = 0
    running = True
    dt = 0
    brush_type = "circle"
    last_pos = None
    is_drawing = False
    stroke_dirty = False
    undo_width = 80
    challenge_button_width = 130
    color_picker_display_color = pygame.Color("#000000")
    confirmation_dialog = None
    challenge_window = None
    color_picker = None
    last_activated_element = None

    manager = pygame_gui.UIManager((width, height), theme_path="theme.json")

    image_brush_cache = {}

    slider = Slider(
        screen,
        10,
        10,
        200,
        40,
        min=0,
        max=99,
        step=1,
        colour=(210, 210, 210),
        handleColour=(120, 120, 120),
        valueColour=(210, 210, 210),
        borderColour=(150, 150, 150),
        borderThickness=10,
        initial=10,
    )

    output = TextBox(screen, 240, 10, 40, 40, fontSize=20)
    output.disable()

    # ================================================
    #              Define Bouding Rects
    # ================================================

    slider_rect = pygame.Rect(0, 0, 250, 60)

    output_rect = pygame.Rect(240, 10, 40, 40)

    tutorial_button_rect = pygame.Rect(0, height - 50, 140, 50)

    tutorial_rect = pygame.Rect(width // 2 - 350, height // 2 - 275, 700, 550)

    undo_button_rect = pygame.Rect(
        width - BUTTON_WIDTH - 2 * undo_width, 0, undo_width, BUTTON_HEIGHT
    )

    redo_button_rect = pygame.Rect(
        width - BUTTON_WIDTH - undo_width, 0, undo_width, BUTTON_HEIGHT
    )

    challenge_button_rect = pygame.Rect(
        width - BUTTON_WIDTH - 2 * undo_width - challenge_button_width,
        0,
        challenge_button_width,
        BUTTON_HEIGHT,
    )

    color_picker_button_rect = pygame.Rect(
        width - BUTTON_WIDTH, height - BUTTON_HEIGHT, BUTTON_WIDTH, BUTTON_HEIGHT
    )

    clear_button_rect = pygame.Rect(
        width - BUTTON_WIDTH, 0, BUTTON_WIDTH, BUTTON_HEIGHT
    )

    circle_brush_button_rect = pygame.Rect(
        width - BUTTON_WIDTH,
        height - 3 * BUTTON_HEIGHT - 2,
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
    )

    image_brush_button_rect = pygame.Rect(
        width - BUTTON_WIDTH,
        height - 4 * BUTTON_HEIGHT - 3,
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
    )

    erase_button_rect = pygame.Rect(
        width - BUTTON_WIDTH,
        height - 2 * BUTTON_HEIGHT - 1,
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
    )

    inner_rect = color_picker_button_rect.inflate(-4, -4)

    # ================================================
    #              Define Actual Buttons
    # ================================================

    undo_button = UIButton(
        relative_rect=undo_button_rect,
        text="",
        manager=manager,
        object_id="#undo_button",
    )
    undo_button.disable()

    redo_button = UIButton(
        relative_rect=redo_button_rect,
        text="",
        manager=manager,
        object_id="#redo_button",
    )
    redo_button.disable()

    challenge_button = UIButton(
        relative_rect=challenge_button_rect,
        text="Challenge",
        manager=manager,
        object_id="#challenge_button",
    )

    color_picker_button = UIButton(
        relative_rect=color_picker_button_rect,
        text="",
        manager=manager,
        object_id="#color_picker_button",
    )

    clear_button = UIButton(
        relative_rect=clear_button_rect,
        text="🗑️",
        manager=manager,
        object_id="#clear_button",
    )

    erase_button = UIButton(
        relative_rect=erase_button_rect,
        text="",
        manager=manager,
        object_id="#eraser_button",
    )

    circle_brush_button = UIButton(
        relative_rect=circle_brush_button_rect,
        text="Circle",
        manager=manager,
        object_id="#circle_brush_button",
    )

    image_brush_button = UIButton(
        relative_rect=image_brush_button_rect,
        text="Baptiste",
        manager=manager,
        object_id="#image_brush_button",
    )

    tutorial_button = UIButton(
        relative_rect=tutorial_button_rect, text="Tutorial", manager=manager
    )

    with open("tutorial.html", "r") as file:
        tutorial_content = file.read()

    tutorial_box = UITextBox(
        tutorial_content, tutorial_rect, manager=manager, visible=0
    )

    # ================================================
    #              Helper Functions
    # ================================================

    def clear_canvas():

        nonlocal current_state

        canvas.fill(pygame.Color("#ffffff"))

        current_state = push_canvas_state(canvas_states, current_state, canvas)

        undo_button.enable()
        redo_button.disable()

    def launch_challenge(difficulty):

        nonlocal current_state

        print(f"Challenge selected: {difficulty}")

        # Placeholder for the future challenge.

        canvas.fill(pygame.Color("#ffffff"))

        font = pygame.font.Font(None, 64)

        title = font.render(f"{difficulty} challenge", True, pygame.Color("#000000"))

        subtitle = font.render("PLACEHOLDER", True, pygame.Color("#666666"))

        canvas.blit(title, title.get_rect(center=(width // 2, height // 2 - 40)))

        canvas.blit(subtitle, subtitle.get_rect(center=(width // 2, height // 2 + 30)))

        current_state = push_canvas_state(canvas_states, current_state, canvas)

        undo_button.enable()
        redo_button.disable()

    def launch_easy():
        launch_challenge("EASY")

    def launch_medium():
        launch_challenge("MEDIUM")

    def launch_hard():
        launch_challenge("HARD")

    def is_over_ui(pos):
        return (
            slider_rect.collidepoint(pos)
            or output_rect.collidepoint(pos)
            or erase_button_rect.collidepoint(pos)
            or undo_button_rect.collidepoint(pos)
            or redo_button_rect.collidepoint(pos)
            or challenge_button_rect.collidepoint(pos)
            or color_picker_button_rect.collidepoint(pos)
            or clear_button_rect.collidepoint(pos)
            or circle_brush_button_rect.collidepoint(pos)
            or image_brush_button_rect.collidepoint(pos)
            or tutorial_button_rect.collidepoint(pos)
            or (tutorial_rect.collidepoint(pos) if tutorial_box.visible else False)
        )

    def get_hovered_element(pos):
        """Return whichever clickable UI element (if any) contains pos.

        When a popup window (clear confirmation, challenge, colour picker)
        is open, only that popup's own buttons - including its title-bar
        close ("X") button - are reachable, mirroring how a real click
        can't reach the toolbar underneath a modal window.
        """

        popup_elements = []

        if confirmation_dialog is not None:
            popup_elements += [
                confirmation_dialog.close_window_button,
                confirmation_dialog.confirm_button,
                confirmation_dialog.cancel_button,
            ]

        if challenge_window is not None:
            popup_elements += [
                challenge_window.close_window_button,
                challenge_window.easy_button,
                challenge_window.medium_button,
                challenge_window.hard_button,
            ]

        if color_picker is not None:
            popup_elements += [
                color_picker.close_window_button,
                getattr(color_picker, "ok_button", None),
                getattr(color_picker, "cancel_button", None),
            ]

        if popup_elements:
            candidates = popup_elements
        else:
            candidates = [
                undo_button if undo_button.is_enabled else None,
                redo_button if redo_button.is_enabled else None,
                challenge_button,
                color_picker_button,
                clear_button,
                circle_brush_button,
                image_brush_button,
                erase_button,
                tutorial_button,
            ]

        for element in candidates:
            if element is not None and element.rect.collidepoint(pos):
                return element

        return None

    def activate_element(element):
        """Fire the same event pygame_gui posts when this element is clicked.

        This lets every existing click handler (ours, the popup windows',
        and pygame_gui's own colour picker) run completely unchanged.
        """

        pygame.event.post(
            pygame.event.Event(
                pygame_gui.UI_BUTTON_PRESSED,
                {
                    "ui_element": element,
                    "ui_object_id": element.most_specific_combined_id,
                },
            )
        )

    def update_slider_from_point(pos):
        """Move the brush-size slider's handle to follow a point's x position."""

        slider_x = slider.getX()
        slider_width = slider.getWidth()

        ratio = (pos[0] - slider_x) / slider_width
        ratio = max(0.0, min(1.0, ratio))

        value = slider.round(ratio * (slider.max - slider.min) + slider.min)
        value = max(min(value, slider.max), slider.min)

        slider.setValue(value)

    def close_confirmation():

        nonlocal confirmation_dialog

        confirmation_dialog = None

    def update_color_picker_button(color):
        nonlocal color_picker_display_color
        color_picker_display_color = pygame.Color(color)

    def _make_circular_brush(size):
        size = max(1, int(size))

        if size in image_brush_cache:
            return image_brush_cache[size]

        source_width, source_height = raw_baptiste.get_size()

        crop_size = min(source_width, source_height)
        crop_x = (source_width - crop_size) // 2
        crop_y = (source_height - crop_size) // 2

        cropped = raw_baptiste.subsurface(
            pygame.Rect(crop_x, crop_y, crop_size, crop_size)
        ).copy()

        diameter = size * 2
        brush = pygame.transform.smoothscale(
            cropped, (diameter, diameter)
        ).convert_alpha()

        mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)

        pygame.draw.circle(mask, (255, 255, 255, 255), (size, size), size)

        brush.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        image_brush_cache[size] = brush

        return brush

    def draw_image_brush(position, size):
        brush = _make_circular_brush(size)
        brush_rect = brush.get_rect(center=position)

        canvas.blit(brush, brush_rect)

    def draw_interpolated(last_pos, current_pos, drawing_size):
        distance = pygame.Vector2(current_pos).distance_to(last_pos)

        step = max(drawing_size / 4, 1)
        steps = max(int(distance / step), 1)

        for i in range(steps + 1):
            t = i / steps

            x = int(last_pos[0] + (current_pos[0] - last_pos[0]) * t)
            y = int(last_pos[1] + (current_pos[1] - last_pos[1]) * t)

            position = (x, y)

            if brush_type == "circle":
                pygame.draw.circle(
                    canvas,
                    drawing_color,
                    position,
                    drawing_size
                )
            elif brush_type == "image":
                draw_image_brush(position, drawing_size)

    def on_colour_changed(colour):
        nonlocal selected_color, drawing_color
        selected_color = pygame.Color(colour)
        drawing_color = pygame.Color(colour)
        update_color_picker_button(selected_color)


    def close_color_picker():
        nonlocal color_picker
        color_picker = None

    # ================================================
    #                  Game Loop
    # ================================================
    last_coord = None
    while running:
        coord = image_subscriber.latest_coord

        drawing_size = max(1, int(slider.getValue()))

        # A new Kinect coordinate was received
        if len(coord) != 0 and coord != last_coord:
            current_time = time.monotonic()

            # If we haven't received a point for a while,
            # consider this the beginning of a new stroke.
            if previous_point is None or current_time - previous_point > nb_buffered_time:
                last_pos = None

            last_coord = coord
            previous_point = current_time

            any_popup_open = (
                confirmation_dialog is not None
                or challenge_window is not None
                or color_picker is not None
            )

            if not any_popup_open and slider_rect.collidepoint(coord):
                # Over the brush-size slider: drag its handle continuously
                # rather than treating it as a discrete button click.
                update_slider_from_point(coord)

                last_activated_element = None
                is_drawing = False
                last_pos = None
            else:
                hovered_element = get_hovered_element(coord)

                if hovered_element is not None:
                    # Only fire once per "entry" onto the element, so
                    # lingering on it doesn't repeatedly re-trigger the
                    # action. Moving off and back on (or onto a different
                    # element) re-arms it.
                    if hovered_element is not last_activated_element:
                        activate_element(hovered_element)

                    last_activated_element = hovered_element
                    is_drawing = False
                    last_pos = None
                elif any_popup_open:
                    # A modal popup is open and the point isn't over any of
                    # its buttons: don't let it draw on the canvas behind it.
                    last_activated_element = None
                    is_drawing = False
                    last_pos = None
                else:
                    last_activated_element = None
                    is_drawing = True

        if (
            is_drawing
            and previous_point is not None
            and time.monotonic() - previous_point > nb_buffered_time
        ):
            is_drawing = False
            last_pos = None

        events = pygame.event.get()

        for event in events:
            manager.process_events(event)

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame_gui.UI_WINDOW_CLOSE:
                if event.ui_element == confirmation_dialog:
                    confirmation_dialog = None

                if event.ui_element == challenge_window:
                    challenge_window = None

                if event.ui_element == color_picker:
                    color_picker = None

            if event.type == pygame_gui.UI_COLOUR_PICKER_COLOUR_PICKED:
                picked_color = pygame.Color(event.colour)
                selected_color = pygame.Color(picked_color)
                drawing_color = pygame.Color(picked_color)

                update_color_picker_button(selected_color)

                if color_picker is not None:
                    color_picker.kill()
                    color_picker = None

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == clear_button and confirmation_dialog is None:
                    confirmation_dialog = ClearConfirmationWindow(
                        pygame.Rect(width // 2 - 300, height // 2 - 175, 600, 350),
                        manager=manager,
                        on_confirm=clear_canvas,
                        on_close=close_confirmation,
                    )

                if event.ui_element == color_picker_button and color_picker is None:
                    color_picker = RadialColorPickerWindow(
                        pygame.Rect(width // 10, height // 10, 8 * width // 10, 8 * height // 10),
                        manager=manager,
                        initial_colour=selected_color,
                        on_colour_changed=on_colour_changed,
                        on_close=close_color_picker,
                    )

                if event.ui_element == challenge_button and challenge_window is None:
                    challenge_window = ChallengeWindow(
                        pygame.Rect(width // 2 - 200, height // 2 - 180, 400, 360),
                        manager=manager,
                        on_easy=launch_easy,
                        on_medium=launch_medium,
                        on_hard=launch_hard,
                    )

                if event.ui_element == circle_brush_button:
                    brush_type = "circle"
                    drawing_color = pygame.Color(selected_color)

                if event.ui_element == image_brush_button:
                    brush_type = "image"
                    drawing_color = pygame.Color(selected_color)

                if event.ui_element == erase_button:
                    drawing_color = pygame.Color("#ffffff")

                if event.ui_element == tutorial_button:
                    if tutorial_box.visible:
                        tutorial_box.hide()
                    else:
                        tutorial_box.show()

                if event.ui_element == undo_button:
                    if current_state > 0:
                        current_state -= 1

                        canvas = canvas_states[current_state].copy()

                        redo_button.enable()

                        if current_state == 0:
                            undo_button.disable()

                if event.ui_element == redo_button:
                    if current_state < len(canvas_states) - 1:
                        current_state += 1

                        canvas = canvas_states[current_state].copy()

                        undo_button.enable()

                        if current_state == len(canvas_states) - 1:
                            redo_button.disable()

        if is_drawing:
            current_pos = coord

            if not is_over_ui(current_pos):
                if last_pos is None:
                    if brush_type == "circle":
                        pygame.draw.circle(
                            canvas,
                            drawing_color,
                            current_pos,
                            drawing_size
                        )
                    elif brush_type == "image":
                        draw_image_brush(current_pos, drawing_size)

                elif not is_over_ui(last_pos):
                    draw_interpolated(
                        last_pos,
                        current_pos,
                        drawing_size
                    )

                last_pos = current_pos
                stroke_dirty = True

        if (
            not is_drawing
            and stroke_dirty
        ):
            current_state = push_canvas_state(
                canvas_states,
                current_state,
                canvas
            )

            undo_button.enable()
            redo_button.disable()

            stroke_dirty = False

        screen.blit(canvas, (0, 0))
        manager.update(dt)
        manager.draw_ui(screen)

        color = color_picker_display_color

        border_color = color.lerp(pygame.Color("#000000"), 0.25)
        pygame.draw.rect(
            screen, border_color, color_picker_button_rect, border_radius=4
        )
        pygame.draw.rect(screen, color, inner_rect, border_radius=3)

        brightness = (color.r * 299 + color.g * 587 + color.b * 114) / 1000
        text_color = (
            pygame.Color("#000000") if brightness > 128 else pygame.Color("#ffffff")
        )
        font = pygame.font.Font(None, 28)
        color_text = font.render("Color", True, text_color)
        screen.blit(
            color_text, color_text.get_rect(center=color_picker_button_rect.center)
        )

        output.setText(str(slider.getValue()))
        pygame_widgets.update(events)
        eraser_rect = eraser_icon.get_rect(center=erase_button_rect.center)
        screen.blit(eraser_icon, eraser_rect)
        pygame.display.flip()

        dt = clock.tick(60) / 1000

    pygame.quit()


if __name__ == "__main__":
    main()
import os
import threading
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sign_dir = BASE_DIR / "signs"
from datetime import datetime

import image_subscriber
import pygame
import pygame_gui
import pygame_widgets
from clearwindow import ClearConfirmationWindow
from emailwindow import EmailWindow
from pygame_gui.elements import UIButton, UITextBox
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from send_email import send_canvas_by_email

BUTTON_WIDTH = 80
BUTTON_HEIGHT = 50
MAX_HISTORY = 20
HOVER_INDICATOR_PADDING = 8  # how much wider the hover circle is than the brush


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

    COLORS = [
        ("B", "#000000"),
        ("G", "#808080"),
        ("B", "#0000ff"),
        ("C", "#00ffff"),
        ("G", "#00ff00"),
        ("Y", "#ffff00"),
        ("R", "#ff0000"),
        ("M", "#ff00ff"),
    ]

    canvas = pygame.Surface((width, height))
    canvas.fill(pygame.Color("#ffffff"))

    raw_baptiste = pygame.image.load(sign_dir / "baptiste.png").convert_alpha()
    epita_icon = pygame.transform.smoothscale(raw_baptiste, (60, 40))
    hover_surface = pygame.Surface((width, height), pygame.SRCALPHA)

    raw_trash = pygame.image.load("signs/poubelle.png").convert_alpha()
    trash_icon = pygame.transform.smoothscale(raw_trash, (30, 20))

    raw_eraser = pygame.image.load(sign_dir / "eraser.png").convert_alpha()
    eraser_icon = pygame.transform.smoothscale(raw_eraser, (60, 40))

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
    selected_tool = "circle"
    last_pos = None
    is_drawing = False
    stroke_dirty = False
    undo_width = 80
    confirmation_dialog = None
    email_window = None

    manager = pygame_gui.UIManager((width, height), theme_path=BASE_DIR / "theme.json")
    # ================================================
    #                 Color Palette
    # ================================================

    image_brush_cache = {}

    slider = Slider(
        screen,
        BUTTON_WIDTH + 10 + 10 + 250,
        10,
        width - 2 * BUTTON_WIDTH - 40 - 500,
        BUTTON_HEIGHT - 20,
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

    # ================================================
    #              Define Bouding Rects
    # ================================================

    slider_rect = pygame.Rect(BUTTON_WIDTH + 10 + 10, 10, width - 2 * BUTTON_WIDTH - 40, BUTTON_HEIGHT)

    # tutorial_button_rect = pygame.Rect(0, height - 50, 140, 50)

    # tutorial_rect = pygame.Rect(width // 2 - 350, height // 2 - 275, 700, 550)

    undo_button_rect = pygame.Rect(
        width // 2 - 10 - undo_width, height - BUTTON_HEIGHT - 10, undo_width, BUTTON_HEIGHT
    )

    redo_button_rect = pygame.Rect(
        width // 2 + 10, height - BUTTON_HEIGHT - 10, undo_width, BUTTON_HEIGHT
    )

    # toolbar_rect = pygame.Rect(width - BUTTON_WIDTH - 24, 0, BUTTON_WIDTH + 24, height)

    # pygame.draw.rect(screen, pygame.Color("#F4F7FB"), toolbar_rect)

    # ================================================
    #                 Color Palette
    # ================================================

    COLOR_BUTTON_WIDTH = BUTTON_WIDTH
    COLOR_BUTTON_HEIGHT = 50

    color_button_rects = []
    color_buttons = []

    palette_x = width - BUTTON_WIDTH
    palette_y = 100

    for index, (name, color_hex) in enumerate(COLORS):

        rect = pygame.Rect(
            width - COLOR_BUTTON_WIDTH - 10,
            20 + (20 + COLOR_BUTTON_HEIGHT) * index,
            COLOR_BUTTON_WIDTH,
            COLOR_BUTTON_HEIGHT,
        )

        color_button_rects.append(rect)

        button = UIButton(
            relative_rect=rect,
            text="",
            manager=manager,
            object_id=f"#color_button_{name.lower()}",
        )

        color_buttons.append(button)

    clear_button_rect = pygame.Rect(
        width - BUTTON_WIDTH - 10, height - BUTTON_HEIGHT - 10, BUTTON_WIDTH, BUTTON_HEIGHT
    )

    save_rect = pygame.Rect(
        10, height - BUTTON_HEIGHT - 10, BUTTON_WIDTH, BUTTON_HEIGHT
    )

    # ============================================================
    # Bottom-right tool buttons
    # ============================================================

    circle_brush_button_rect = pygame.Rect(
        10,
        height // 2 - 3 * BUTTON_HEIGHT - 50,
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
    )

    image_brush_button_rect = pygame.Rect(
        10,
        height // 2 - BUTTON_HEIGHT // 2 - 50,
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
    )

    epita_icon_rect = pygame.Rect(
        10 + BUTTON_WIDTH // 2 - 30,
        height // 2 - BUTTON_HEIGHT // 2 - 50 + BUTTON_HEIGHT // 2 - 18,
        60,
        40,
    )

    erase_button_rect = pygame.Rect(
        10,
        height // 2 + 2 * BUTTON_HEIGHT - 50,
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
    )

    erase_icon_rect = pygame.Rect(
        10 + BUTTON_WIDTH // 2 - 15,
        height // 2 + 2 * BUTTON_HEIGHT - 50 + BUTTON_HEIGHT // 2 - 10,
        30,
        20,
    )

    trash_icon_rect = pygame.Rect(
        width - BUTTON_WIDTH // 2 - 10 - 15, height - BUTTON_HEIGHT // 2 - 20, 30, 20
    )

    # ================================================
    #      Bounding boxes for button groups
    # ================================================

    TOOLBOX_PADDING = 20
    TOOLBOX_FACTOR = 1.2

    left_tool_rects = [circle_brush_button_rect, image_brush_button_rect, erase_button_rect]
    left_toolbox_rect = left_tool_rects[0].unionall(left_tool_rects[1:]).inflate(
        TOOLBOX_PADDING * TOOLBOX_FACTOR, TOOLBOX_PADDING * 2
    )
    left_toolbox_rect.left = max(0, left_toolbox_rect.left)

    right_toolbox_rect = color_button_rects[0].unionall(color_button_rects[1:]).inflate(
        TOOLBOX_PADDING * TOOLBOX_FACTOR, TOOLBOX_PADDING * 2
    )
    right_toolbox_rect.right = min(width, right_toolbox_rect.right)

    toolbox_font = pygame.font.Font(None, 28)
    tools_label_surface = toolbox_font.render("Tools", True, pygame.Color("#000000"))
    colors_label_surface = toolbox_font.render("Colors", True, pygame.Color("#000000"))

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

    clear_button = UIButton(
        relative_rect=clear_button_rect,
        text="",
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
        text="",
        manager=manager,
        object_id="#circle_brush_button",
    )

    image_brush_button = UIButton(
        relative_rect=image_brush_button_rect,
        text="",
        manager=manager,
        object_id="#image_brush_button",
    )

    # tutorial_button = UIButton(
    #     relative_rect=tutorial_button_rect, text="Tutorial", manager=manager
    # )

    save_button = UIButton(relative_rect=save_rect, text="Save", manager=manager)
    # with open(BASE_DIR / "tutorial.html", "r") as file:
    #     tutorial_content = file.read()

    # tutorial_box = UITextBox(
    #     tutorial_content, tutorial_rect, manager=manager, visible=0
    # )

    # ================================================
    #              Helper Functions
    # ================================================

    def clear_canvas():
        nonlocal current_state

        canvas.fill(pygame.Color("#ffffff"))

        current_state = push_canvas_state(canvas_states, current_state, canvas)

        undo_button.enable()
        redo_button.disable()

    def is_over_ui(pos):
        if (
            slider_rect.collidepoint(pos)
            or erase_button_rect.collidepoint(pos)
            or undo_button_rect.collidepoint(pos)
            or redo_button_rect.collidepoint(pos)
            or clear_button_rect.collidepoint(pos)
            or circle_brush_button_rect.collidepoint(pos)
            or image_brush_button_rect.collidepoint(pos)
            # or tutorial_button_rect.collidepoint(pos)
            or save_rect.collidepoint(pos)
        ):
            return True

        for rect in color_button_rects:
            if rect.collidepoint(pos):
                return True

        # if tutorial_box.visible and tutorial_rect.collidepoint(pos):
        #     return True

        return False

    def get_hovered_element(pos):
        """Return the UI element underneath the Kinect cursor."""

        popup_elements = []

        if confirmation_dialog is not None:
            popup_elements += [
                confirmation_dialog.close_window_button,
                confirmation_dialog.confirm_button,
                confirmation_dialog.cancel_button,
            ]

        if email_window is not None:
            popup_elements += [
                email_window.close_window_button,
            ]

        if popup_elements:
            candidates = popup_elements
        else:
            candidates = [
                undo_button if undo_button.is_enabled else None,
                redo_button if redo_button.is_enabled else None,
                clear_button,
                circle_brush_button,
                image_brush_button,
                erase_button,
                # tutorial_button,
                save_button,
            ]

            candidates += color_buttons

        for element in candidates:
            if element is not None and element.rect.collidepoint(pos):
                return element

        return None

    def select_color(color):
        nonlocal selected_color, drawing_color

        selected_color = pygame.Color(color)
        drawing_color = pygame.Color(selected_color)

    def activate_element(element):
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

    def _make_image_brush(size):
        size = max(1, int(size))

        if size in image_brush_cache:
            return image_brush_cache[size]

        source_width, source_height = raw_baptiste.get_size()

        # Keep the original aspect ratio.
        scale_factor = size / source_height

        brush_width = max(1, int(source_width * scale_factor))
        brush_height = max(1, int(source_height * scale_factor))

        brush = pygame.transform.smoothscale(
            raw_baptiste, (brush_width, brush_height)
        ).convert_alpha()

        image_brush_cache[size] = brush

        return brush

    def draw_image_brush(position, size):
        brush = _make_image_brush(size)
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
                pygame.draw.circle(canvas, drawing_color, position, drawing_size)
            elif brush_type == "image":
                draw_image_brush(position, drawing_size)

    def save_canvas():
        os.makedirs("saves", exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"saves/painting_{timestamp}.png"
        pygame.image.save(canvas, filename)
        print(f"Canvas saved as {filename}")

    def close_email_window():
        nonlocal email_window
        email_window = None

    def send_current_canvas(recipient):
        nonlocal email_window

        recipient = recipient.strip()

        if "@" not in recipient or "." not in recipient:
            print("Please enter a valid email address.")
            return

        success, message = send_canvas_by_email(canvas, recipient)
        print(message)

        if email_window is not None:
            email_window.kill()
            email_window = None

    # ================================================
    #                  Game Loop
    # ================================================
    last_coord = None
    hovered_element = None
    pressed_element = None
    while running:
        any_popup_open = (
            confirmation_dialog is not None
            or email_window is not None
            # or tutorial_box.visible
        )
        coord = image_subscriber.latest_coord
        drawing_size = max(1, int(slider.getValue()))

        is_touching = image_subscriber.finger_on_table

        # ============================================================
        # Kinect interaction
        # ============================================================

        if len(coord) != 0 and coord != last_coord:
            current_time = time.monotonic()

            if (
                previous_point is None
                or current_time - previous_point > nb_buffered_time
            ):
                last_pos = None

            last_coord = coord
            previous_point = current_time

            any_popup_open = (
                confirmation_dialog is not None
                or email_window is not None
                # or tutorial_box.visible
            )

            # --------------------------------------------------------
            # Slider
            # --------------------------------------------------------

            if not any_popup_open and slider_rect.collidepoint(coord):
                update_slider_from_point(coord)

                hovered_element = None
                pressed_element = None
                is_drawing = False
                last_pos = None

            else:
                # ----------------------------------------------------
                # Find what the Kinect cursor is hovering
                # ----------------------------------------------------

                new_hovered_element = get_hovered_element(coord)

                # Update hover state even when we are NOT touching.
                hovered_element = new_hovered_element

                # ----------------------------------------------------
                # Button pressing
                # ----------------------------------------------------

                if is_touching:
                    if hovered_element is not None:
                        # Only trigger once when the finger first touches
                        # a button.
                        if pressed_element is not hovered_element:
                            pressed_element = hovered_element
                            activate_element(hovered_element)

                        is_drawing = False
                        last_pos = None

                    elif any_popup_open:
                        pressed_element = None
                        is_drawing = False
                        last_pos = None

                    else:
                        pressed_element = None
                        is_drawing = True

                else:
                    # Finger is NOT touching the table.
                    # Therefore nothing gets activated.
                    pressed_element = None

                    # If hovering a button, don't draw.
                    if hovered_element is not None:
                        is_drawing = False
                        last_pos = None

                    elif any_popup_open:
                        is_drawing = False
                        last_pos = None

                    else:
                        is_drawing = False

        else:
            # No new Kinect coordinate.
            # Don't repeatedly press anything.
            if not is_touching:
                pressed_element = None

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

            if event.type == pygame.MOUSEBUTTONDOWN:
                if (
                    not is_over_ui(event.pos)
                    and confirmation_dialog is None
                    # and not tutorial_box.visible
                    and email_window is None
                ):
                    is_drawing = True
                    last_pos = event.pos

            if event.type == pygame.MOUSEBUTTONUP:
                if stroke_dirty:
                    current_state = push_canvas_state(
                        canvas_states, current_state, canvas
                    )

                    undo_button.enable()
                    redo_button.disable()

                is_drawing = False
                last_pos = None
                stroke_dirty = False

            if event.type == pygame_gui.UI_WINDOW_CLOSE:
                if event.ui_element == confirmation_dialog:
                    confirmation_dialog = None

                #       if event.ui_element == challenge_window:
                #          challenge_window = None

                if event.ui_element == email_window:
                    email_window = None

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                for index, button in enumerate(color_buttons):
                    if event.ui_element == button:
                        _, color_hex = COLORS[index]
                        select_color(color_hex)
                        break

                if event.ui_element == clear_button and confirmation_dialog is None:
                    confirmation_dialog = ClearConfirmationWindow(
                        pygame.Rect(width // 2 - 300, height // 2 - 175, 600, 350),
                        manager=manager,
                        on_confirm=clear_canvas,
                        on_close=close_confirmation,
                    )

                if event.ui_element == circle_brush_button:
                    brush_type = "circle"
                    selected_tool = "circle"
                    drawing_color = pygame.Color(selected_color)

                if event.ui_element == image_brush_button:
                    brush_type = "image"
                    selected_tool = "image"
                    drawing_color = pygame.Color(selected_color)

                if event.ui_element == erase_button:
                    selected_tool = "eraser"
                    brush_type = "circle"
                    drawing_color = pygame.Color("#ffffff")

                # if event.ui_element == tutorial_button:
                #     if tutorial_box.visible:
                #         tutorial_box.hide()
                #     else:
                #         tutorial_box.show()

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

                if event.ui_element == save_button and email_window is None:
                    save_canvas()
                    email_window = EmailWindow(
                        pygame.Rect(width // 2 - 220, height // 2 - 110, 440, 220),
                        manager=manager,
                        on_send=send_current_canvas,
                        on_close=close_email_window,
                    )

        table_touching = image_subscriber.finger_on_table

        if is_drawing and table_touching:
            current_pos = coord

            if not is_over_ui(current_pos):
                if last_pos is None:
                    if brush_type == "circle":
                        pygame.draw.circle(
                            canvas, drawing_color, current_pos, drawing_size
                        )
                    elif brush_type == "image":
                        draw_image_brush(current_pos, drawing_size)

                elif not is_over_ui(last_pos):
                    draw_interpolated(last_pos, current_pos, drawing_size)

                last_pos = current_pos
                stroke_dirty = True
        elif not table_touching:
            last_pos = None

        if not is_drawing and stroke_dirty:
            current_state = push_canvas_state(canvas_states, current_state, canvas)

            undo_button.enable()
            redo_button.disable()

            stroke_dirty = False
            last_pos = current_pos

        screen.blit(canvas, (0, 0))
        screen.blit(hover_surface, (0, 0))

        manager.update(dt)
        manager.draw_ui(screen)

        # ============================================================
        # Bounding boxes for tool / color groups
        # ============================================================

        pygame.draw.rect(screen, pygame.Color("#303030"), left_toolbox_rect, width=2, border_radius=8)
        screen.blit(
            tools_label_surface,
            tools_label_surface.get_rect(midbottom=(left_toolbox_rect.centerx, left_toolbox_rect.top - 6)),
        )

        pygame.draw.rect(screen, pygame.Color("#303030"), right_toolbox_rect, width=2, border_radius=8)
        screen.blit(
            colors_label_surface,
            colors_label_surface.get_rect(midbottom=(right_toolbox_rect.centerx, right_toolbox_rect.top - 6)),
        )

        # ============================================================
        # Custom color buttons
        # ============================================================

        for index, (name, color_hex) in enumerate(COLORS):
            rect = color_button_rects[index]
            color = pygame.Color(color_hex)

            is_hovered = hovered_element is color_buttons[index]
            is_pressed = pressed_element is color_buttons[index]

            # Selected color gets a stronger border.
            is_selected = color == selected_color

            if is_pressed:
                border_color = pygame.Color("#ffffff")
                border_width = 5
                inner_rect = rect.inflate(-8, -8)

            elif is_selected:
                border_color = pygame.Color("#000000")
                border_width = 5
                inner_rect = rect.inflate(-8, -8)

            elif is_hovered:
                border_color = pygame.Color("#ffffff")
                border_width = 4
                inner_rect = rect.inflate(-6, -6)

            else:
                border_color = pygame.Color("#303030")
                border_width = 2
                inner_rect = rect.inflate(-4, -4)

            # Outer border
            pygame.draw.rect(
                screen,
                border_color,
                rect,
                width=border_width,
                border_radius=4,
            )

            # Button background
            pygame.draw.rect(
                screen,
                color,
                inner_rect,
                border_radius=3,
            )

            # Slight pressed effect
            if is_pressed:
                overlay = pygame.Surface(inner_rect.size, pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 45))
                screen.blit(overlay, inner_rect)

            # Text brightness
            brightness = (color.r * 299 + color.g * 587 + color.b * 114) / 1000

            text_color = (
                pygame.Color("#000000") if brightness > 128 else pygame.Color("#ffffff")
            )

            font = pygame.font.Font(None, 24)

            text_surface = font.render(
                name,
                True,
                text_color,
            )

            screen.blit(
                text_surface,
                text_surface.get_rect(center=rect.center),
            )

        # ============================================================
        # Custom tool buttons
        # ============================================================

        tool_buttons = [
            ("CIRCLE", circle_brush_button, circle_brush_button_rect, "circle"),
            ("", image_brush_button, image_brush_button_rect, "image"),
            ("", erase_button, erase_button_rect, "eraser"),
        ]

        tool_font = pygame.font.Font(None, 26)

        for name, button, rect, tool_type in tool_buttons:
            is_hovered = hovered_element is button
            is_pressed = pressed_element is button
            is_selected = selected_tool == tool_type

            # Selected tool = black border
            if is_pressed:
                border_color = pygame.Color("#ffffff")
                border_width = 5
                background_color = pygame.Color("#505050")

            elif is_selected:
                border_color = pygame.Color("#000000")
                border_width = 5
                background_color = pygame.Color("#d0d0d0")

            elif is_hovered:
                border_color = pygame.Color("#ffffff")
                border_width = 4
                background_color = pygame.Color("#b0b0b0")

            else:
                border_color = pygame.Color("#303030")
                border_width = 2
                background_color = pygame.Color("#eeeeee")

            inner_rect = rect.inflate(-border_width * 2, -border_width * 2)

            # Outer border
            pygame.draw.rect(
                screen,
                border_color,
                rect,
                width=border_width,
                border_radius=5,
            )

            # Button background
            pygame.draw.rect(
                screen,
                background_color,
                inner_rect,
                border_radius=3,
            )

            # Pressed visual effect
            if is_pressed:
                overlay = pygame.Surface(inner_rect.size, pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 45))
                screen.blit(overlay, inner_rect)

            # Text
            text_color = pygame.Color("#000000")

            text_surface = tool_font.render(
                name,
                True,
                text_color,
            )

            screen.blit(
                text_surface,
                text_surface.get_rect(center=rect.center),
            )

        # ============================================================
        # Kinect cursor — MUST BE LAST
        # ============================================================

        hover_surface.fill((0, 0, 0, 0))

        if len(coord) > 0:
            hover_pos = (int(coord[0]), int(coord[1]))

            if pressed_element is not None:
                cursor_color = (255, 255, 255, 230)
                cursor_width = 5
            elif hovered_element is not None:
                cursor_color = (255, 255, 255, 210)
                cursor_width = 3
            else:
                cursor_color = (255, 255, 255, 180)
                cursor_width = 3

            hover_radius = drawing_size + HOVER_INDICATOR_PADDING

            pygame.draw.circle(
                hover_surface,
                cursor_color,
                hover_pos,
                hover_radius,
                width=cursor_width,
            )

            pygame.draw.circle(
                hover_surface,
                (0, 0, 0, 180),
                hover_pos,
                hover_radius,
                width=2,
            )

        pygame_widgets.update(events)
        trash_icon_rect = trash_icon.get_rect(center=trash_icon_rect.center)
        screen.blit(trash_icon, trash_icon_rect)
        epita_icon_rect = epita_icon.get_rect(center=epita_icon_rect.center)
        screen.blit(epita_icon, epita_icon_rect)
        erase_icon_rect = eraser_icon.get_rect(center=erase_icon_rect.center)
        screen.blit(eraser_icon, erase_icon_rect)
        screen.blit(hover_surface, (0, 0))
        pygame.display.flip()

        dt = clock.tick(60) / 1000

    pygame.quit()


if __name__ == "__main__":
    main()

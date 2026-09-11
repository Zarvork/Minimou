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
COLOR_BUTTON_WIDTH = BUTTON_WIDTH
COLOR_BUTTON_HEIGHT = 50
UNDO_WIDTH = 80
TOOLBOX_PADDING = 20
TOOLBOX_FACTOR = 1.2
MAX_HISTORY = 20  # how many undo/redos are possible
HOVER_INDICATOR_PADDING = 8  # how much wider the hover circle is than the brush


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


class GameManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((width, height))
        self.manager = pygame_gui.UIManager(
            (width, height), theme_path=BASE_DIR / "theme.json"
        )
        self.canvas = pygame.Surface((width, height))
        self.canvas.fill(pygame.Color("#ffffff"))
        self.selected_color = pygame.Color("#000000")
        self.drawing_color = pygame.Color(self.selected_color)


def select_color(game_manager, color):
    game_manager.selected_color = pygame.Color(color)
    game_manager.drawing_color = pygame.Color(game_manager.selected_color)


GAME_BUTTONS = {}


def load_game_buttons(game_manager):
    global GAME_BUTTONS
    GAME_BUTTONS["undo"] = UIButton(
        relative_rect=GAME_RECTS["undo"],
        text="",
        manager=game_manager.manager,
        object_id="#undo_button",
    )
    GAME_BUTTONS["undo"].disable()

    GAME_BUTTONS["redo"] = UIButton(
        relative_rect=GAME_RECTS["redo"],
        text="",
        manager=game_manager.manager,
        object_id="#redo_button",
    )
    GAME_BUTTONS["redo"].disable()

    GAME_BUTTONS["clear"] = UIButton(
        relative_rect=GAME_RECTS["clear"],
        text="",
        manager=game_manager.manager,
        object_id="#clear_button",
    )

    GAME_BUTTONS["erase"] = UIButton(
        relative_rect=GAME_RECTS["erase"],
        text="",
        manager=game_manager.manager,
        object_id="#eraser_button",
    )

    GAME_BUTTONS["circle_brush"] = UIButton(
        relative_rect=GAME_RECTS["circle_brush"],
        text="",
        manager=game_manager.manager,
        object_id="#circle_brush_button",
    )

    GAME_BUTTONS["image_brush"] = UIButton(
        relative_rect=GAME_RECTS["image_brush"],
        text="",
        manager=game_manager.manager,
        object_id="#image_brush_button",
    )

    GAME_BUTTONS["save"] = UIButton(
        relative_rect=GAME_RECTS["save"], text="Save", manager=game_manager.manager
    )

    for index, (name, _) in enumerate(COLORS):
        button = UIButton(
            relative_rect=GAME_RECTS[f"color_{index}"],
            text="",
            manager=game_manager.manager,
            object_id=f"#color_button_{name.lower()}",
        )

        GAME_BUTTONS[f"color_{index}"] = button


GAME_RECTS = {}


def load_bounding_boxes(width, height):
    global GAME_RECTS

    GAME_RECTS["slider"] = pygame.Rect(
        BUTTON_WIDTH + 10 + 10, 10, width - 2 * BUTTON_WIDTH - 40, BUTTON_HEIGHT
    )

    GAME_RECTS["undo"] = pygame.Rect(
        width // 2 - 10 - UNDO_WIDTH,
        height - BUTTON_HEIGHT - 10,
        UNDO_WIDTH,
        BUTTON_HEIGHT,
    )

    GAME_RECTS["redo"] = pygame.Rect(
        width // 2 + 10, height - BUTTON_HEIGHT - 10, UNDO_WIDTH, BUTTON_HEIGHT
    )

    GAME_RECTS["clear"] = pygame.Rect(
        width - 2 * BUTTON_WIDTH - 10,
        height - BUTTON_HEIGHT - 10,
        2 * BUTTON_WIDTH,
        BUTTON_HEIGHT,
    )

    GAME_RECTS["save"] = pygame.Rect(
        10, height - BUTTON_HEIGHT - 10, 2 * BUTTON_WIDTH, BUTTON_HEIGHT
    )

    GAME_RECTS["circle_brush"] = pygame.Rect(
        10,
        height // 2 - 3 * BUTTON_HEIGHT - 50,
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
    )

    GAME_RECTS["image_brush"] = pygame.Rect(
        10,
        height // 2 - BUTTON_HEIGHT // 2 - 50,
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
    )

    GAME_RECTS["epita_icon"] = pygame.Rect(
        10 + BUTTON_WIDTH // 2 - 30,
        height // 2 - 50 - 18,
        60,
        40,
    )

    GAME_RECTS["erase"] = pygame.Rect(
        10,
        height // 2 + 2 * BUTTON_HEIGHT - 50,
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
    )

    GAME_RECTS["erase_icon"] = pygame.Rect(
        10 + BUTTON_WIDTH // 2 - 15,
        height // 2 + 2 * BUTTON_HEIGHT - 50 + BUTTON_HEIGHT // 2 - 10,
        30,
        20,
    )

    GAME_RECTS["trash_icon"] = pygame.Rect(
        width - BUTTON_WIDTH - 10 - 10, height - BUTTON_HEIGHT // 2 - 20, 20, 20
    )

    left_tool_rects = [
        GAME_RECTS["circle_brush"],
        GAME_RECTS["image_brush"],
        GAME_RECTS["erase"],
    ]
    left_toolbox_rect = (
        left_tool_rects[0]
        .unionall(left_tool_rects[1:])
        .inflate(TOOLBOX_PADDING * TOOLBOX_FACTOR, TOOLBOX_PADDING * 2)
    )
    left_toolbox_rect.left = max(0, left_toolbox_rect.left)

    color_button_rects = []

    for index, (name, color_hex) in enumerate(COLORS):
        rect = pygame.Rect(
            width - COLOR_BUTTON_WIDTH - 10,
            20 + (20 + COLOR_BUTTON_HEIGHT) * index,
            COLOR_BUTTON_WIDTH,
            COLOR_BUTTON_HEIGHT,
        )

        GAME_RECTS[f"color_{index}"] = rect
        color_button_rects.append(rect)

    right_toolbox_rect = (
        color_button_rects[0]
        .unionall(color_button_rects[1:])
        .inflate(TOOLBOX_PADDING * TOOLBOX_FACTOR, TOOLBOX_PADDING * 2)
    )
    right_toolbox_rect.right = min(width, right_toolbox_rect.right)

    GAME_RECTS["left_toolbox"] = left_toolbox_rect
    GAME_RECTS["right_toolbox"] = right_toolbox_rect


ICONS = {}

raw_baptiste = None


def load_icons():
    global ICONS, raw_baptiste
    raw_baptiste = pygame.image.load(sign_dir / "baptiste.png").convert_alpha()
    ICONS["epita"] = pygame.transform.smoothscale(raw_baptiste, (60, 40))

    raw_trash = pygame.image.load("signs/poubelle.png").convert_alpha()
    ICONS["trash"] = pygame.transform.smoothscale(raw_trash, (20, 20))

    raw_eraser = pygame.image.load(sign_dir / "eraser.png").convert_alpha()
    ICONS["eraser"] = pygame.transform.smoothscale(raw_eraser, (60, 40))


def push_canvas_state(states, index, canvas):
    """
    Pushes a new state of the canvas to the list `states`

    used for the undo/redo mechanic
    """

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

    game_manager = GameManager(1280, 720)
    screen = game_manager.screen
    width, height = screen.get_size()
    canvas = game_manager.canvas

    load_icons()
    load_bounding_boxes(width, height)
    load_game_buttons(game_manager)

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
    confirmation_dialog = None
    email_window = None

    # ================================================
    #              Slider and toolboxes
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

    toolbox_font = pygame.font.Font(None, 28)

    hover_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    tools_label_surface = toolbox_font.render("Tools", True, pygame.Color("#000000"))
    colors_label_surface = toolbox_font.render("Colors", True, pygame.Color("#000000"))

    # ================================================
    #              Helper Functions
    # ================================================

    def clear_canvas():
        """
        Function called when the clear button is pressed.

        Clears the canves and allows to undo
        """
        nonlocal canvas
        nonlocal current_state

        canvas.fill(pygame.Color("#ffffff"))

        current_state = push_canvas_state(
            canvas_states, current_state, game_manager.canvas
        )

        GAME_BUTTONS["undo"].enable()
        GAME_BUTTONS["redo"].disable()

    def is_over_ui(pos):
        """
        Returns True if the position is on a Button of the scene
        """
        if (
            GAME_RECTS["slider"].collidepoint(pos)
            or GAME_RECTS["erase"].collidepoint(pos)
            or GAME_RECTS["undo"].collidepoint(pos)
            or GAME_RECTS["redo"].collidepoint(pos)
            or GAME_RECTS["clear"].collidepoint(pos)
            or GAME_RECTS["circle_brush"].collidepoint(pos)
            or GAME_RECTS["image_brush"].collidepoint(pos)
            or GAME_RECTS["save"].collidepoint(pos)
        ):
            return True

        for index in range(len(COLORS)):
            rect = GAME_RECTS[f"color_{index}"]
            if rect.collidepoint(pos):
                return True

        return False

    def get_hovered_element(pos):
        """
        Return the UI element underneath the Kinect cursor.
        """
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
                email_window.send_button,
                email_window.cancel_button,
            ]

        if popup_elements:
            candidates = popup_elements
        else:
            candidates = [
                GAME_BUTTONS["undo"] if GAME_BUTTONS["undo"].is_enabled else None,
                GAME_BUTTONS["redo"] if GAME_BUTTONS["redo"].is_enabled else None,
                GAME_BUTTONS["clear"],
                GAME_BUTTONS["circle_brush"],
                GAME_BUTTONS["image_brush"],
                GAME_BUTTONS["erase"],
                GAME_BUTTONS["save"],
            ]

            for index in range(len(COLORS)):
                candidates.append(GAME_BUTTONS[f"color_{index}"])

        for element in candidates:
            if element is not None and element.rect.collidepoint(pos):
                return element

        return None

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
        """
        Move the brush-size slider's handle to follow a point's x position.
        """

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
                pygame.draw.circle(
                    canvas, game_manager.drawing_color, position, drawing_size
                )
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
        any_popup_open = confirmation_dialog is not None or email_window is not None
        coord = image_subscriber.latest_coord
        drawing_size = max(1, int(slider.getValue()))

        is_touching = image_subscriber.finger_on_table

        # ============================================================
        # Kinect interaction
        # ============================================================
        if len(coord) != 0 and coord != last_coord:  # Received an input
            current_time = time.monotonic()

            if (
                previous_point is None
                or current_time - previous_point > nb_buffered_time
            ):
                last_pos = None

            last_coord = coord
            previous_point = current_time

            any_popup_open = confirmation_dialog is not None or email_window is not None

            # --------------------------------------------------------
            # Slider
            # --------------------------------------------------------

            if not any_popup_open and GAME_RECTS["slider"].collidepoint(coord):
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
                hovered_element = new_hovered_element

                # ----------------------------------------------------
                # Button pressing
                # ----------------------------------------------------
                if is_touching:
                    if hovered_element is not None:
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

        # ===============================================
        # Handle Event Interactions
        # ===============================================
        events = pygame.event.get()
        for event in events:
            game_manager.manager.process_events(event)

            if event.type == pygame.QUIT:
                running = False

            # ===============================================
            # Mouse Interaction
            # ===============================================
            # Still needed for the save button
            if event.type == pygame.MOUSEBUTTONDOWN:
                if (
                    not is_over_ui(event.pos)
                    and confirmation_dialog is None
                    and email_window is None
                ):
                    is_drawing = True
                    last_pos = event.pos
            if event.type == pygame.MOUSEBUTTONUP:
                if stroke_dirty:
                    current_state = push_canvas_state(
                        canvas_states, current_state, canvas
                    )

                    GAME_BUTTONS["undo"].enable()
                    GAME_BUTTONS["redo"].disable()

                is_drawing = False
                last_pos = None
                stroke_dirty = False

            # ===============================================
            # Close Windows
            # ===============================================
            if event.type == pygame_gui.UI_WINDOW_CLOSE:
                if event.ui_element == confirmation_dialog:
                    confirmation_dialog = None

                if event.ui_element == email_window:
                    email_window = None

            # ===============================================
            # Button Interaction
            # ===============================================
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                for index in range(len(COLORS)):
                    button = GAME_BUTTONS[f"color_{index}"]
                    if event.ui_element == button:
                        _, color_hex = COLORS[index]
                        select_color(game_manager, color_hex)
                        break

                if (
                    event.ui_element == GAME_BUTTONS["clear"]
                    and confirmation_dialog is None
                ):
                    confirmation_dialog = ClearConfirmationWindow(
                        pygame.Rect(width // 2 - 300, height // 2 - 175, 600, 350),
                        manager=game_manager.manager,
                        on_confirm=clear_canvas,
                        on_close=close_confirmation,
                    )

                if event.ui_element == GAME_BUTTONS["circle_brush"]:
                    brush_type = "circle"
                    selected_tool = "circle"
                    game_manager.drawing_color = pygame.Color(
                        game_manager.selected_color
                    )

                if event.ui_element == GAME_BUTTONS["image_brush"]:
                    brush_type = "image"
                    selected_tool = "image"
                    game_manager.drawing_color = pygame.Color(
                        game_manager.selected_color
                    )

                if event.ui_element == GAME_BUTTONS["erase"]:
                    selected_tool = "eraser"
                    brush_type = "circle"
                    game_manager.drawing_color = pygame.Color("#ffffff")

                if event.ui_element == GAME_BUTTONS["undo"]:
                    if current_state > 0:
                        current_state -= 1

                        canvas = canvas_states[current_state].copy()

                        GAME_BUTTONS["redo"].enable()

                        if current_state == 0:
                            GAME_BUTTONS["undo"].disable()

                if event.ui_element == GAME_BUTTONS["redo"]:
                    if current_state < len(canvas_states) - 1:
                        current_state += 1

                        canvas = canvas_states[current_state].copy()

                        GAME_BUTTONS["undo"].enable()

                        if current_state == len(canvas_states) - 1:
                            GAME_BUTTONS["redo"].disable()

                if event.ui_element == GAME_BUTTONS["save"] and email_window is None:
                    save_canvas()
                    email_window = EmailWindow(
                        pygame.Rect(width // 2 - 220, height // 2 - 110, 440, 220),
                        manager=game_manager.manager,
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
                            canvas,
                            game_manager.drawing_color,
                            current_pos,
                            drawing_size,
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

            GAME_BUTTONS["undo"].enable()
            GAME_BUTTONS["redo"].disable()

            stroke_dirty = False
            last_pos = current_pos

        screen.blit(canvas, (0, 0))
        screen.blit(hover_surface, (0, 0))

        game_manager.manager.update(dt)
        game_manager.manager.draw_ui(screen)

        # ============================================================
        # Bounding boxes for tool / color groups
        # ============================================================

        pygame.draw.rect(
            screen,
            pygame.Color("#303030"),
            GAME_RECTS["left_toolbox"],
            width=2,
            border_radius=8,
        )
        screen.blit(
            tools_label_surface,
            tools_label_surface.get_rect(
                midbottom=(
                    GAME_RECTS["left_toolbox"].centerx,
                    GAME_RECTS["left_toolbox"].top - 6,
                )
            ),
        )

        pygame.draw.rect(
            screen,
            pygame.Color("#303030"),
            GAME_RECTS["right_toolbox"],
            width=2,
            border_radius=8,
        )
        screen.blit(
            colors_label_surface,
            colors_label_surface.get_rect(
                midbottom=(
                    GAME_RECTS["right_toolbox"].centerx,
                    GAME_RECTS["right_toolbox"].top - 6,
                )
            ),
        )

        # ============================================================
        # Custom color buttons
        # ============================================================

        for index, (name, color_hex) in enumerate(COLORS):
            rect = GAME_RECTS[f"color_{index}"]
            color = pygame.Color(color_hex)

            is_hovered = hovered_element is GAME_RECTS[f"color_{index}"]
            is_pressed = pressed_element is GAME_RECTS[f"color_{index}"]

            # Selected color gets a stronger border.
            is_selected = color == game_manager.selected_color

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
            (
                "CIRCLE",
                GAME_BUTTONS["circle_brush"],
                GAME_RECTS["circle_brush"],
                "circle",
            ),
            ("", GAME_BUTTONS["image_brush"], GAME_RECTS["image_brush"], "image"),
            ("", GAME_BUTTONS["erase"], GAME_RECTS["erase"], "eraser"),
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
        # Kinect cursor
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

        trash_icon_rect = GAME_RECTS["trash_icon"]
        epita_icon_rect = GAME_RECTS["epita_icon"]
        erase_icon_rect = GAME_RECTS["erase_icon"]
        trash_icon_rect = ICONS["trash"].get_rect(center=trash_icon_rect.center)
        screen.blit(ICONS["trash"], trash_icon_rect)
        epita_icon_rect = ICONS["epita"].get_rect(center=epita_icon_rect.center)
        screen.blit(ICONS["epita"], epita_icon_rect)
        erase_icon_rect = ICONS["eraser"].get_rect(center=erase_icon_rect.center)
        screen.blit(ICONS["eraser"], erase_icon_rect)

        screen.blit(hover_surface, (0, 0))
        pygame.display.flip()

        dt = game_manager.clock.tick(60) / 1000

    pygame.quit()


if __name__ == "__main__":
    main()

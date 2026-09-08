import pygame
import pygame_gui
import pygame_widgets

from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from pygame_widgets.button import Button, ButtonArray
from pygame_gui.elements import UIButton, UITextBox


BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
MAX_HISTORY = 20

texts = [
    "BLACK",
    "GREY",
    "BROWN",
    "MAGENTA",
    "BLUE",
    "CYAN",
    "GREEN",
    "YELLOW",
    "RED",
    ""
]

COLORS = [
    "#000000",
    "#a9a9a9",
    "#a7661d",
    "#ff00ff",
    "#0000ff",
    "#00ffff",
    "#00ff00",
    "#ffff00",
    "#ff0000",
    "#ffffff",
]


def push_canvas_state(states, index, canvas):
    """Add a new canvas state and remove any redo states."""
    del states[index + 1:]
    states.append(canvas.copy())

    if len(states) > MAX_HISTORY:
        states.pop(0)
        index -= 1

    return index + 1

class ClearConfirmationWindow(pygame_gui.elements.UIWindow):
    def __init__(self, rect, manager, on_confirm, on_close):
        super().__init__(
            rect,
            manager=manager,
            window_display_title="Confirm Clear",
            resizable=False,
            draggable=True
        )

        self.on_confirm = on_confirm
        self.on_close = on_close

        container = self.get_container()

        self.message = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                30, 30, rect.width - 60, 70
            ),
            text="Are you sure you want to clear the canvas?",
            manager=manager,
            container=container
        )

        self.confirm_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                30, 120, rect.width - 60, 55
            ),
            text="CLEAR",
            manager=manager,
            container=container
        )

        self.cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                30, 190, rect.width - 60, 55
            ),
            text="CANCEL",
            manager=manager,
            container=container
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


class ColorPickerWindow(pygame_gui.elements.UIWindow):
    def __init__(self, rect, manager, on_confirm, on_close):
        super().__init__(
            rect,
            manager=manager,
            window_display_title="Confirm Color Change",
            resizable=False,
            draggable=True
        )

        self.on_confirm = on_confirm
        self.on_close = on_close

        container = self.get_container()

        self.message = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                30, 30, rect.width - 60, 70
            ),
            text="Are you sure you want to clear the canvas?",
            manager=manager,
            container=container
        )

        self.confirm_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                30, 120, rect.width - 60, 55
            ),
            text="CLEAR",
            manager=manager,
            container=container
        )

        self.cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                30, 190, rect.width - 60, 55
            ),
            text="CANCEL",
            manager=manager,
            container=container
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

class MinigameWindow(pygame_gui.elements.UIWindow):
    def __init__(self, rect, manager, easy, medium, hard):
        super().__init__(
            rect,
            manager=manager,
            window_display_title="Confirm Clear",
            resizable=False,
            draggable=True
        )

        self.easy = easy
        self.medium = medium
        self.hard = hard

        container = self.get_container()

        self.message = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                30, 30, rect.width - 60, 70
            ),
            text="Are you sure you want to clear the canvas?",
            manager=manager,
            container=container
        )

        self.confirm_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                30, 120, rect.width - 60, 55
            ),
            text="CLEAR",
            manager=manager,
            container=container
        )

        self.cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                30, 190, rect.width - 60, 55
            ),
            text="CANCEL",
            manager=manager,
            container=container
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

def main():
    pygame.init()

    screen = pygame.display.set_mode((1280, 720))
    width, height = screen.get_size()

    clock = pygame.time.Clock()
    running = True
    dt = 0

    drawing_color = "#000000"
    brush_type = "circle"

    # ---------------------------------------------------------
    # Image brush
    # ---------------------------------------------------------

    raw_baptiste = pygame.image.load(
        "baptiste.jpg"
    ).convert()

    image_brush_cache = {}

    def make_circular_brush(size):
        """
        Create a circular version of the Baptiste image.

        The image is cropped to a square first so its aspect ratio
        is preserved, then resized and given a circular alpha mask.
        """

        size = max(1, int(size))

        if size in image_brush_cache:
            return image_brush_cache[size]

        source_width, source_height = raw_baptiste.get_size()

        crop_size = min(source_width, source_height)

        crop_x = (source_width - crop_size) // 2
        crop_y = (source_height - crop_size) // 2

        cropped = raw_baptiste.subsurface(
            pygame.Rect(
                crop_x,
                crop_y,
                crop_size,
                crop_size
            )
        ).copy()

        brush = pygame.transform.smoothscale(
            cropped,
            (size * 2, size * 2)
        ).convert_alpha()

        mask = pygame.Surface(
            (size * 2, size * 2),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            mask,
            (255, 255, 255, 255),
            (size, size),
            size
        )

        brush.blit(
            mask,
            (0, 0),
            special_flags=pygame.BLEND_RGBA_MULT
        )

        image_brush_cache[size] = brush

        return brush


    def draw_image_brush(position, size):
        brush = make_circular_brush(size)

        brush_rect = brush.get_rect(
            center=position
        )

        canvas.blit(
            brush,
            brush_rect
        )

    last_pos = None
    is_drawing = False
    stroke_dirty = False

    canvas = pygame.Surface((width, height))
    canvas.fill("#ffffff")

    manager = pygame_gui.UIManager(
        (width, height),
        theme_path="theme.json"
    )

    def draw_image_brush(position, size):
        brush = pygame.transform.smoothscale(
            image_brush,
            (size * 2, size * 2)
        )

        brush_rect = brush.get_rect(
            center=position
        )

        canvas.blit(brush, brush_rect)

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
        initial=10
    )

    output = TextBox(
        screen,
        240,
        10,
        40,
        40,
        fontSize=20
    )
    output.disable()

    slider_rect = pygame.Rect(0, 0, 250, 60)
    output_rect = pygame.Rect(240, 10, 40, 40)

    raw_baptiste = pygame.image.load(
        "baptiste.jpg"
    ).convert()

    image_brush = raw_baptiste

    # ---------------------------------------------------------
    # Undo / redo
    # ---------------------------------------------------------

    undo_width = 80
    undo_button_layout = pygame.Rect(
        width - BUTTON_WIDTH - 2 * undo_width,
        0,
        undo_width,
        BUTTON_HEIGHT
    )

    redo_button_layout = pygame.Rect(
        width - BUTTON_WIDTH - undo_width,
        0,
        undo_width,
        BUTTON_HEIGHT
    )

    # ---------------------------------------------------------
    # Right-side controls
    # ---------------------------------------------------------

    ui_panel_rect = pygame.Rect(
        width - BUTTON_WIDTH,
        0,
        BUTTON_WIDTH,
        height
    )

    clear_button_layout = pygame.Rect(
        width - BUTTON_WIDTH,
        0,
        BUTTON_WIDTH,
        BUTTON_HEIGHT
    )

    clear_button = UIButton(
        relative_rect=clear_button_layout,
        text="🗑️",
        manager=manager,
        object_id="#clear_button"
    )

    # ---------------------------------------------------------
    # Color buttons using ButtonArray
    # ---------------------------------------------------------
    #
    # ButtonArray calls the appropriate callback automatically,
    # so we don't need:
    #
    #     for i, button in enumerate(color_buttons):
    #
    # in the event loop.
    #
    # ---------------------------------------------------------

    color_array_y = BUTTON_HEIGHT
    color_array_height = height - BUTTON_HEIGHT


    def select_color(color, index):
        nonlocal drawing_color
        drawing_color = color

        for i, button in enumerate(color_button_array.buttons):
            button.setText(texts[i])
            button.radius = 1
        color_button_array.buttons[index].radius = 20
        color_button_array.buttons[index].setText(texts[index] + " <--")


    color_callbacks = tuple(
        lambda color=color, index=i: select_color(color, index)
        for i, color in enumerate(COLORS)
    )

    color_button_array = ButtonArray(
        screen,
        width - BUTTON_WIDTH,
        color_array_y,
        BUTTON_WIDTH,
        color_array_height,
        (1, len(COLORS)),
        border=3,
        texts=texts,
        onClicks=color_callbacks
    )

    for button, color in zip(color_button_array.buttons, COLORS):
        if color == "#ffffff":
            raw_eraser = pygame.image.load(
                "eraser.png"
            ).convert_alpha()

            eraser_size = (
                BUTTON_WIDTH - 20,
                40
            )

            eraser_icon = pygame.transform.smoothscale(
                raw_eraser,
                eraser_size
            )

            button.image = eraser_icon
            color = "#4a4a4a"

        pygame_color = pygame.Color(color)

        # Normal state
        button.inactiveColour = pygame_color

        # Hover state: slightly darker
        button.hoverColour = pygame_color.lerp(pygame.Color("#000000"), 0.2)

        # Pressed state: even darker
        button.pressedColour = pygame_color.lerp(pygame.Color("#000000"), 0.35)

        # Automatically choose readable text
        brightness = (
            pygame_color.r * 299
            + pygame_color.g * 587
            + pygame_color.b * 114
        ) / 1000

        button.textColour = (
            pygame.Color("#000000")
            if brightness > 128
            else pygame.Color("#ffffff")
        )



    # ---------------------------------------------------------
    # Eraser button
    # ---------------------------------------------------------
    #
    # Button(image=...) expects a pygame.Surface, not a filename.
    # ---------------------------------------------------------


    # ---------------------------------------------------------
    # Tutorial button
    # ---------------------------------------------------------

    circle_brush_button_layout = pygame.Rect(
        0,
        height - 100,
        140,
        50
    )

    image_brush_button_layout = pygame.Rect(
        0,
        height - 150,
        140,
        50
    )

    undo_button = UIButton(
        relative_rect=undo_button_layout,
        text="",
        manager=manager,
        object_id="#undo_button"
    )

    redo_button = UIButton(
        relative_rect=redo_button_layout,
        text="",
        manager=manager,
        object_id="#redo_button"
    )

    circle_brush_button = UIButton(
        relative_rect=circle_brush_button_layout,
        text="Circle",
        manager=manager,
        object_id="#circle_brush_button"
    )

    image_brush_button = UIButton(
        relative_rect=image_brush_button_layout,
        text="Baptiste",
        manager=manager,
        object_id="#image_brush_button"
    )

    tutorial_button_rect = pygame.Rect(
        0,
        height - 50,
        140,
        50
    )

    tutorial_button = UIButton(
        relative_rect=tutorial_button_rect,
        text="Tutorial",
        manager=manager
    )

    tutorial_rect = pygame.Rect(
        width // 2 - 350,
        height // 2 - 275,
        700,
        550
    )

    # Tutorial text box.
    #
    # visible=0 means it starts hidden.
    tutorial_box = UITextBox(
        """
        <b>Drawing App Tutorial</b><br><br>

        <b>Drawing</b><br>
        Click and drag on the white canvas to draw.
        The brush follows your mouse smoothly.<br><br>

        <b>Brush size</b><br>
        Use the slider in the top-left corner to change
        the size of your brush.<br><br>

        <b>Colors</b><br>
        Select a color from the buttons on the right side
        of the screen.<br><br>

        <b>Eraser</b><br>
        Click the eraser button in the bottom-left corner.
        It changes the drawing color to white.<br><br>

        <b>Undo / Redo</b><br>
        Undo removes your most recent stroke.
        Redo restores a stroke that was undone.<br><br>

        <b>Clear</b><br>
        Click Clear to erase the entire canvas.
        You will be asked to confirm first.<br><br>

        <b>Tip</b><br>
        You can use the tutorial button again to hide
        this window.
        """,
        tutorial_rect,
        manager=manager,
        visible=0
    )

    # ---------------------------------------------------------
    # Canvas history
    # ---------------------------------------------------------

    canvas_states = [canvas.copy()]
    current_state = 0

    def clear_canvas():
        nonlocal current_state

        canvas.fill("#ffffff")

        current_state = push_canvas_state(
            canvas_states,
            current_state,
            canvas
        )

        undo_button.enable()
        redo_button.disable()

    undo_button.disable()
    redo_button.disable()

    # ---------------------------------------------------------
    # Confirmation dialog
    # ---------------------------------------------------------

    confirmation_dialog = None

    # ---------------------------------------------------------
    # UI collision helper
    # ---------------------------------------------------------

    def is_over_ui(pos):
        return (
            slider_rect.collidepoint(pos)
            or output_rect.collidepoint(pos)
            or ui_panel_rect.collidepoint(pos)
            or undo_button_layout.collidepoint(pos)
            or redo_button_layout.collidepoint(pos)
            or circle_brush_button_layout.collidepoint(pos)
            or image_brush_button_layout.collidepoint(pos)
            or tutorial_button_rect.collidepoint(pos)
            or (
                tutorial_rect.collidepoint(pos)
                if tutorial_box.visible
                else False
            )
        )

    # ---------------------------------------------------------
    # Main loop
    # ---------------------------------------------------------

    def set_confirmation_none():
        nonlocal confirmation_dialog
        confirmation_dialog = None

    while running:

        drawing_size = max(1, int(slider.getValue()))

        events = pygame.event.get()

        for event in events:

            # -------------------------------------------------
            # Quit
            # -------------------------------------------------

            if event.type == pygame.QUIT:
                running = False

            # -------------------------------------------------
            # Mouse drawing
            # -------------------------------------------------

            if event.type == pygame.MOUSEBUTTONDOWN:
                if (
                    not is_over_ui(event.pos)
                    and confirmation_dialog is None
                    and not tutorial_box.visible
                ):
                    is_drawing = True
                    last_pos = event.pos

            if event.type == pygame.MOUSEBUTTONUP:
                if stroke_dirty:
                    current_state = push_canvas_state(
                        canvas_states,
                        current_state,
                        canvas
                    )

                    undo_button.enable()
                    redo_button.disable()

                is_drawing = False
                last_pos = None
                stroke_dirty = False

            if event.type == pygame_gui.UI_WINDOW_CLOSE:
                if event.ui_element == confirmation_dialog:
                    confirmation_dialog = None
            # -------------------------------------------------
            # pygame_gui events
            # -------------------------------------------------

            if event.type == pygame_gui.UI_BUTTON_PRESSED:

                # Clear
                if (
                    event.ui_element == clear_button
                    and confirmation_dialog is None
                ):
                    confirmation_dialog = ClearConfirmationWindow(
                        pygame.Rect(
                            width // 2 - 300,
                            height // 2 - 175,
                            600,
                            350
                        ),
                        manager=manager,
                        on_confirm=clear_canvas,
                        on_close=lambda: set_confirmation_none()
                    )

                if event.ui_element == image_brush_button:
                    brush_type = "image"

                if event.ui_element == circle_brush_button:
                    brush_type = "circle"

                # Tutorial
                if event.ui_element == tutorial_button:

                    if tutorial_box.visible:
                        tutorial_box.hide()
                    else:
                        tutorial_box.show()

                # Undo
                if event.ui_element == undo_button:

                    if current_state > 0:
                        current_state -= 1

                        canvas = canvas_states[
                            current_state
                        ].copy()

                        redo_button.enable()

                        if current_state == 0:
                            undo_button.disable()

                # Redo
                if event.ui_element == redo_button:

                    if current_state < len(canvas_states) - 1:
                        current_state += 1

                        canvas = canvas_states[
                            current_state
                        ].copy()

                        undo_button.enable()

                        if current_state == len(canvas_states) - 1:
                            redo_button.disable()

            # -------------------------------------------------
            # Close confirmation dialog
            # -------------------------------------------------

            if event.type == pygame_gui.UI_WINDOW_CLOSE:

                if event.ui_element == confirmation_dialog:
                    confirmation_dialog = None

            # Let pygame_gui process the event
            manager.process_events(event)

        # -----------------------------------------------------
        # Draw on canvas
        # -----------------------------------------------------

        if is_drawing:

            current_pos = pygame.mouse.get_pos()

            if not is_over_ui(current_pos):

                if (
                    last_pos is not None
                    and not is_over_ui(last_pos)
                ):

                    distance = pygame.Vector2(
                        current_pos
                    ).distance_to(last_pos)

                    step = max(drawing_size / 4, 1)
                    steps = max(
                        int(distance / step),
                        1
                    )

                    for i in range(steps + 1):

                        t = i / steps

                        interp_x = (
                            last_pos[0]
                            + (
                                current_pos[0]
                                - last_pos[0]
                            ) * t
                        )

                        interp_y = (
                            last_pos[1]
                            + (
                                current_pos[1]
                                - last_pos[1]
                            ) * t
                        )

                        if brush_type == "circle":
                            pygame.draw.circle(
                                canvas,
                                drawing_color,
                                (
                                    int(interp_x),
                                    int(interp_y)
                                ),
                                drawing_size
                            )

                        elif brush_type == "image":
                            draw_image_brush(
                                (
                                    int(interp_x),
                                    int(interp_y)
                                ),
                                drawing_size
                            )

                    stroke_dirty = True

            last_pos = current_pos

        # -----------------------------------------------------
        # Render
        # -----------------------------------------------------

        screen.blit(canvas, (0, 0))

        manager.update(dt)
        manager.draw_ui(screen)

        output.setText(str(slider.getValue()))

        # pygame_widgets must be updated once per frame.
        # This handles the ButtonArray and erase button.
        pygame_widgets.update(events)

        pygame.display.flip()

        dt = clock.tick(60) / 1000

    pygame.quit()


if __name__ == "__main__":
    main()

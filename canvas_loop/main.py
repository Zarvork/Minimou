import pygame
import pygame_gui
import pygame_widgets

from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from pygame_widgets.button import ButtonArray
from pygame_gui.elements import UIButton, UITextBox
from pygame_gui.windows import UIColourPickerDialog


BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
MAX_HISTORY = 20


TEXTS = [
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
    """Confirmation window shown before clearing the canvas."""

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

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                30,
                30,
                rect.width - 60,
                70
            ),
            text="Are you sure you want to clear the canvas?",
            manager=manager,
            container=container
        )

        self.confirm_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                30,
                120,
                rect.width - 60,
                55
            ),
            text="CLEAR",
            manager=manager,
            container=container
        )

        self.cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                30,
                190,
                rect.width - 60,
                55
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


def main():

    pygame.init()

    screen = pygame.display.set_mode((1280, 720))
    width, height = screen.get_size()

    clock = pygame.time.Clock()

    running = True
    dt = 0

    # =========================================================
    # Drawing state
    # =========================================================

    selected_color = pygame.Color("#000000")

    # The colour currently being used to draw.
    # This can temporarily be white when the eraser is selected.
    drawing_color = pygame.Color(selected_color)

    brush_type = "circle"

    last_pos = None
    is_drawing = False
    stroke_dirty = False

    # =========================================================
    # Canvas
    # =========================================================

    canvas = pygame.Surface(
        (width, height)
    )

    canvas.fill(
        pygame.Color("#ffffff")
    )

    # =========================================================
    # pygame_gui
    # =========================================================

    manager = pygame_gui.UIManager(
        (width, height),
        theme_path="theme.json"
    )

    # =========================================================
    # Image brush
    # =========================================================

    try:
        raw_baptiste = pygame.image.load(
            "baptiste.jpg"
        ).convert()
    except pygame.error as error:

        print(
            "Could not load baptiste.jpg:"
        )
        print(error)

        raw_baptiste = pygame.Surface(
            (100, 100)
        )

        raw_baptiste.fill(
            pygame.Color("#888888")
        )

    image_brush_cache = {}

    def make_circular_brush(size):
        """
        Create a circular image brush.

        The source image is cropped to a square,
        resized and masked into a circle.
        """

        size = max(
            1,
            int(size)
        )

        if size in image_brush_cache:
            return image_brush_cache[size]

        source_width, source_height = (
            raw_baptiste.get_size()
        )

        crop_size = min(
            source_width,
            source_height
        )

        crop_x = (
            source_width - crop_size
        ) // 2

        crop_y = (
            source_height - crop_size
        ) // 2

        cropped = raw_baptiste.subsurface(
            pygame.Rect(
                crop_x,
                crop_y,
                crop_size,
                crop_size
            )
        ).copy()

        diameter = size * 2

        brush = pygame.transform.smoothscale(
            cropped,
            (
                diameter,
                diameter
            )
        ).convert_alpha()

        mask = pygame.Surface(
            (
                diameter,
                diameter
            ),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            mask,
            (255, 255, 255, 255),
            (
                size,
                size
            ),
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

        brush = make_circular_brush(
            size
        )

        brush_rect = brush.get_rect(
            center=position
        )

        canvas.blit(
            brush,
            brush_rect
        )

    # =========================================================
    # Brush size slider
    # =========================================================

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

    slider_rect = pygame.Rect(
        0,
        0,
        250,
        60
    )

    output_rect = pygame.Rect(
        240,
        10,
        40,
        40
    )

    # =========================================================
    # Undo / redo
    # =========================================================

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

    # =========================================================
    # Challenge
    # =========================================================

    challenge_button_width = 130

    challenge_button_layout = pygame.Rect(
        width
        - BUTTON_WIDTH
        - 2 * undo_width
        - challenge_button_width,
        0,
        challenge_button_width,
        BUTTON_HEIGHT
    )

    challenge_button = UIButton(
        relative_rect=challenge_button_layout,
        text="Challenge",
        manager=manager,
        object_id="#challenge_button"
    )

    # =========================================================
    # Color picker
    # =========================================================

    color_picker_button_layout = pygame.Rect(
        width - BUTTON_WIDTH,
        height - BUTTON_HEIGHT,
        BUTTON_WIDTH,
        BUTTON_HEIGHT
    )

    color_picker_button = UIButton(
        relative_rect=color_picker_button_layout,
        text="",
        manager=manager,
        object_id="#color_picker_button"
    )

    color_picker_display_color = pygame.Color("#000000")


    def update_color_picker_button(color):
        nonlocal color_picker_display_color
        color_picker_display_color = pygame.Color(color)

    # =========================================================
    # Clear button
    # =========================================================

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

    # =========================================================
    # Eraser
    #
    # The eraser image is NOT placed inside the pygame_gui
    # button. Instead, the button is only used as a transparent
    # click target and the icon is drawn manually.
    #
    # This prevents theme.json from replacing the icon when
    # the mouse hovers over the button.
    # =========================================================

    erase_button_layout = pygame.Rect(
        width - BUTTON_WIDTH,
        height - 2 * BUTTON_HEIGHT - 1,
        BUTTON_WIDTH,
        BUTTON_HEIGHT
    )

    erase_button = UIButton(
        relative_rect=erase_button_layout,
        text="",
        manager=manager,
        object_id="#eraser_button"
    )

    try:

        raw_eraser = pygame.image.load(
            "eraser.png"
        ).convert_alpha()

        eraser_icon = pygame.transform.smoothscale(
            raw_eraser,
            (
                BUTTON_WIDTH - 20,
                40
            )
        )

    except pygame.error as error:

        print(
            "Could not load eraser.png:"
        )
        print(error)

        eraser_icon = pygame.Surface(
            (
                BUTTON_WIDTH - 20,
                40
            ),
            pygame.SRCALPHA
        )

    # =========================================================
    # Brush buttons
    # =========================================================

    circle_brush_button_layout = pygame.Rect(
        width - BUTTON_WIDTH,
        height - 3 * BUTTON_HEIGHT - 2,
        BUTTON_WIDTH,
        BUTTON_HEIGHT
    )

    image_brush_button_layout = pygame.Rect(
        width - BUTTON_WIDTH,
        height - 4 * BUTTON_HEIGHT - 3,
        BUTTON_WIDTH,
        BUTTON_HEIGHT
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

    # =========================================================
    # Tutorial
    # =========================================================

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

        <b>Color Picker</b><br>
        Use the Color button to choose any custom color.<br><br>

        <b>Eraser</b><br>
        Click the eraser button to draw with white.<br><br>

        <b>Brushes</b><br>
        Circle uses the normal drawing brush.
        Baptiste uses your image as a circular brush.<br><br>

        <b>Undo / Redo</b><br>
        Undo removes your most recent stroke.
        Redo restores a stroke that was undone.<br><br>

        <b>Challenge</b><br>
        Choose Easy, Medium or Hard to launch a challenge.
        The challenges are currently placeholders.<br><br>

        <b>Clear</b><br>
        Click Clear to erase the entire canvas.
        You will be asked to confirm first.
        """,
        tutorial_rect,
        manager=manager,
        visible=0
    )

    # =========================================================
    # Canvas history
    # =========================================================

    canvas_states = [
        canvas.copy()
    ]

    current_state = 0

    def clear_canvas():

        nonlocal current_state

        canvas.fill(
            pygame.Color("#ffffff")
        )

        current_state = push_canvas_state(
            canvas_states,
            current_state,
            canvas
        )

        undo_button.enable()
        redo_button.disable()

    undo_button.disable()
    redo_button.disable()

    # =========================================================
    # Dialog state
    # =========================================================

    confirmation_dialog = None
    challenge_window = None
    color_picker = None

    # =========================================================
    # Challenge placeholders
    # =========================================================

    def launch_challenge(difficulty):

        nonlocal current_state

        print(
            f"Challenge selected: {difficulty}"
        )

        # Placeholder for the future challenge.

        canvas.fill(
            pygame.Color("#ffffff")
        )

        font = pygame.font.Font(
            None,
            64
        )

        title = font.render(
            f"{difficulty} challenge",
            True,
            pygame.Color("#000000")
        )

        subtitle = font.render(
            "PLACEHOLDER",
            True,
            pygame.Color("#666666")
        )

        canvas.blit(
            title,
            title.get_rect(
                center=(
                    width // 2,
                    height // 2 - 40
                )
            )
        )

        canvas.blit(
            subtitle,
            subtitle.get_rect(
                center=(
                    width // 2,
                    height // 2 + 30
                )
            )
        )

        current_state = push_canvas_state(
            canvas_states,
            current_state,
            canvas
        )

        undo_button.enable()
        redo_button.disable()

    def launch_easy():
        launch_challenge("EASY")

    def launch_medium():
        launch_challenge("MEDIUM")

    def launch_hard():
        launch_challenge("HARD")

    # =========================================================
    # UI collision
    # =========================================================

    def is_over_ui(pos):

        return (
            slider_rect.collidepoint(pos)
            or output_rect.collidepoint(pos)

            or erase_button_layout.collidepoint(pos)

            or undo_button_layout.collidepoint(pos)
            or redo_button_layout.collidepoint(pos)

            or challenge_button_layout.collidepoint(pos)

            or color_picker_button_layout.collidepoint(pos)

            or clear_button_layout.collidepoint(pos)

            or circle_brush_button_layout.collidepoint(pos)
            or image_brush_button_layout.collidepoint(pos)

            or tutorial_button_rect.collidepoint(pos)

            or (
                tutorial_rect.collidepoint(pos)
                if tutorial_box.visible
                else False
            )
        )

    # =========================================================
    # Dialog helpers
    # =========================================================

    def close_confirmation():

        nonlocal confirmation_dialog

        confirmation_dialog = None

    # =========================================================
    # Main loop
    # =========================================================

    while running:

        drawing_size = max(
            1,
            int(slider.getValue())
        )

        events = pygame.event.get()

        for event in events:

            # =================================================
            # Let pygame_gui process the event ONCE
            # =================================================

            manager.process_events(event)

            # =================================================
            # Quit
            # =================================================

            if event.type == pygame.QUIT:

                running = False

            # =================================================
            # Mouse drawing
            # =================================================

            if event.type == pygame.MOUSEBUTTONDOWN:

                if (
                    not is_over_ui(event.pos)
                    and confirmation_dialog is None
                    and challenge_window is None
                    and color_picker is None
                    and not tutorial_box.visible
                ):

                    is_drawing = True
                    last_pos = event.pos

            # =================================================
            # Mouse released
            # =================================================

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

            # =================================================
            # GUI window closed
            # =================================================

            if event.type == pygame_gui.UI_WINDOW_CLOSE:

                if event.ui_element == confirmation_dialog:

                    confirmation_dialog = None

                if event.ui_element == challenge_window:

                    challenge_window = None

                if event.ui_element == color_picker:

                    color_picker = None

            # =================================================
            # COLOR PICKER
            # =================================================
            #
            # Do not require event.ui_element == color_picker.
            #
            # pygame_gui's colour picker can emit this event from
            # one of its internal elements.
            # =================================================

            if event.type == pygame_gui.UI_COLOUR_PICKER_COLOUR_PICKED:

                picked_color = pygame.Color(event.colour)

                # Remember the user's chosen colour.
                # This is NOT changed by the eraser.
                selected_color = pygame.Color(picked_color)

                # Use the newly selected colour for drawing.
                drawing_color = pygame.Color(picked_color)

                # Update the visible Color button.
                update_color_picker_button(
                    selected_color
                )

                if color_picker is not None:

                    color_picker.kill()
                    color_picker = None

            # =================================================
            # pygame_gui buttons
            # =================================================

            if event.type == pygame_gui.UI_BUTTON_PRESSED:

                # -------------------------------------------------
                # Clear
                # -------------------------------------------------

                if (
                    event.ui_element == clear_button
                    and confirmation_dialog is None
                ):

                    confirmation_dialog = (
                        ClearConfirmationWindow(
                            pygame.Rect(
                                width // 2 - 300,
                                height // 2 - 175,
                                600,
                                350
                            ),
                            manager=manager,
                            on_confirm=clear_canvas,
                            on_close=close_confirmation
                        )
                    )

                # -------------------------------------------------
                # Color picker
                # -------------------------------------------------

                if (
                    event.ui_element == color_picker_button
                    and color_picker is None
                ):

                    color_picker = UIColourPickerDialog(
                        pygame.Rect(
                            width // 2 - 250,
                            height // 2 - 250,
                            500,
                            500
                        ),
                        manager=manager,
                        initial_colour=selected_color,
                        window_title="Choose Color"
                    )

                # -------------------------------------------------
                # Challenge
                # -------------------------------------------------

                if (
                    event.ui_element == challenge_button
                    and challenge_window is None
                ):

                    challenge_window = ChallengeWindow(
                        pygame.Rect(
                            width // 2 - 200,
                            height // 2 - 180,
                            400,
                            360
                        ),
                        manager=manager,
                        on_easy=launch_easy,
                        on_medium=launch_medium,
                        on_hard=launch_hard
                    )

                # -------------------------------------------------
                # Circle brush
                # -------------------------------------------------

                if event.ui_element == circle_brush_button:

                    brush_type = "circle"
                    drawing_color = pygame.Color(selected_color)

                # -------------------------------------------------
                # Baptiste brush
                # -------------------------------------------------

                if event.ui_element == image_brush_button:

                    brush_type = "image"
                    drawing_color = pygame.Color(selected_color)

                # -------------------------------------------------
                # Eraser
                # -------------------------------------------------

                if event.ui_element == erase_button:

                    drawing_color = pygame.Color(
                        "#ffffff"
                    )

                # -------------------------------------------------
                # Tutorial
                # -------------------------------------------------

                if event.ui_element == tutorial_button:

                    if tutorial_box.visible:

                        tutorial_box.hide()

                    else:

                        tutorial_box.show()

                # -------------------------------------------------
                # Undo
                # -------------------------------------------------

                if event.ui_element == undo_button:

                    if current_state > 0:

                        current_state -= 1

                        canvas = canvas_states[
                            current_state
                        ].copy()

                        redo_button.enable()

                        if current_state == 0:

                            undo_button.disable()

                # -------------------------------------------------
                # Redo
                # -------------------------------------------------

                if event.ui_element == redo_button:

                    if (
                        current_state
                        < len(canvas_states) - 1
                    ):

                        current_state += 1

                        canvas = canvas_states[
                            current_state
                        ].copy()

                        undo_button.enable()

                        if (
                            current_state
                            == len(canvas_states) - 1
                        ):

                            redo_button.disable()

        # =====================================================
        # Draw
        # =====================================================

        if is_drawing:

            current_pos = pygame.mouse.get_pos()

            if not is_over_ui(current_pos):

                if (
                    last_pos is not None
                    and not is_over_ui(last_pos)
                ):

                    distance = pygame.Vector2(
                        current_pos
                    ).distance_to(
                        last_pos
                    )

                    step = max(
                        drawing_size / 4,
                        1
                    )

                    steps = max(
                        int(distance / step),
                        1
                    )

                    for i in range(
                        steps + 1
                    ):

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

                        position = (
                            int(interp_x),
                            int(interp_y)
                        )

                        # -----------------------------------------
                        # Circle
                        # -----------------------------------------

                        if brush_type == "circle":

                            pygame.draw.circle(
                                canvas,
                                drawing_color,
                                position,
                                drawing_size
                            )

                        # -----------------------------------------
                        # Baptiste
                        # -----------------------------------------

                        elif brush_type == "image":

                            draw_image_brush(
                                position,
                                drawing_size
                            )

                    stroke_dirty = True

            last_pos = current_pos

        # =====================================================
        # Render
        # =====================================================

        screen.blit(
            canvas,
            (0, 0)
        )

        manager.update(dt)
        manager.draw_ui(screen)

        color = color_picker_display_color

        # Slight darkening for the border
        border_color = color.lerp(
            pygame.Color("#000000"),
            0.25
        )

        pygame.draw.rect(
            screen,
            border_color,
            color_picker_button_layout,
            border_radius=4
        )

        inner_rect = color_picker_button_layout.inflate(
            -4,
            -4
        )

        pygame.draw.rect(
            screen,
            color,
            inner_rect,
            border_radius=3
        )

        # Choose readable text colour
        brightness = (
            color.r * 299
            + color.g * 587
            + color.b * 114
        ) / 1000

        text_color = (
            pygame.Color("#000000")
            if brightness > 128
            else pygame.Color("#ffffff")
        )

        font = pygame.font.Font(None, 28)

        color_text = font.render(
            "Color",
            True,
            text_color
        )

        screen.blit(
            color_text,
            color_text.get_rect(
                center=color_picker_button_layout.center
            )
        )

        output.setText(
            str(slider.getValue())
        )

        pygame_widgets.update(
            events
        )

        # =====================================================
        # Draw eraser icon AFTER pygame_gui
        #
        # This is the important part. Since the icon is drawn
        # after manager.draw_ui(), theme.json cannot overwrite it.
        # =====================================================

        eraser_rect = eraser_icon.get_rect(
            center=erase_button_layout.center
        )

        screen.blit(
            eraser_icon,
            eraser_rect
        )

        pygame.display.flip()

        dt = clock.tick(60) / 1000

    pygame.quit()


if __name__ == "__main__":
    main()

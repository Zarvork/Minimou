import colorsys
import math

import pygame
import pygame_gui


_WHEEL_CACHE = {}


def generate_color_wheel(diameter):
    """Build a hue/saturation color wheel (angle = hue, radius = saturation, value = 1).

    Returns an SRCALPHA pygame.Surface, transparent outside the circle.
    Results are cached by diameter since generation is a bit of work.
    """
    if diameter in _WHEEL_CACHE:
        return _WHEEL_CACHE[diameter]

    import numpy as np

    radius = diameter / 2
    yy, xx = np.mgrid[0:diameter, 0:diameter]
    xx = xx - radius
    yy = yy - radius

    dist = np.sqrt(xx ** 2 + yy ** 2)
    angle = np.degrees(np.arctan2(-yy, xx)) % 360

    saturation = np.clip(dist / radius, 0, 1)
    hue = angle / 360.0
    value = np.ones_like(hue)

    h = hue * 6.0
    i = np.floor(h).astype(int) % 6
    f = h - np.floor(h)
    s = saturation
    v = value

    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)

    conditions = [i == k for k in range(6)]
    r = np.select(conditions, [v, q, p, p, t, v])
    g = np.select(conditions, [t, v, v, q, p, p])
    b = np.select(conditions, [p, p, t, v, v, q])

    rgb = np.clip(np.stack([r, g, b], axis=-1), 0, 1)
    rgb_uint8 = (rgb * 255).astype(np.uint8)

    surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    # pygame surfarray wants shape (width, height, 3) -> x is the first axis
    pygame.surfarray.blit_array(surface, rgb_uint8.transpose(1, 0, 2))

    alpha_mask = (dist <= radius).astype(np.uint8) * 255
    alpha_array = pygame.surfarray.pixels_alpha(surface)
    alpha_array[:, :] = alpha_mask.transpose(1, 0)
    del alpha_array  # release the surface lock

    _WHEEL_CACHE[diameter] = surface
    return surface


class RadialColorPickerWindow(pygame_gui.elements.UIWindow):
    """A big circular hue/saturation picker plus a brightness slider.

    Unlike the built-in square + sliders UIColourPickerDialog, every target
    here is large and forgiving — meant for pointing devices (e.g. a Kinect)
    that aren't pixel-precise.
    """

    def __init__(self, rect, manager, initial_colour, on_colour_changed, on_close):
        super().__init__(
            rect,
            manager=manager,
            window_display_title="Choose Color",
            resizable=False,
            draggable=True,
        )

        self.on_colour_changed = on_colour_changed
        self.on_close_callback = on_close
        self.dragging_wheel = False
        self.dragging_brightness = False

        container = self.get_container()

        # The rect passed in is the OUTER window size — the title bar and
        # borders eat into it, so the actual drawable area is smaller and
        # not something we can compute from `rect` alone. Ask the container
        # for its real usable size instead, or content ends up cropped.
        content_rect = container.get_relative_rect()
        content_width = content_rect.width
        content_height = content_rect.height

        margin = 20
        bar_height = 50
        done_height = 55

        wheel_diameter = min(
            content_width - margin * 2,
            content_height - bar_height - done_height - margin * 4,
        )
        wheel_diameter = max(int(wheel_diameter), 100)
        self.wheel_diameter = wheel_diameter
        self.wheel_radius = wheel_diameter / 2

        wheel_x = (content_width - wheel_diameter) // 2
        self.wheel_rect = pygame.Rect(wheel_x, margin, wheel_diameter, wheel_diameter)

        # Keep the pristine wheel separate from what's displayed — the
        # displayed copy gets a selection marker drawn on top of it.
        self._base_wheel_surface = generate_color_wheel(wheel_diameter)
        self.wheel_image = pygame_gui.elements.UIImage(
            relative_rect=self.wheel_rect,
            image_surface=self._base_wheel_surface,
            manager=manager,
            container=container,
        )

        # Starting hue/saturation/value, derived from the initial color
        r, g, b, _ = initial_colour.normalize()
        self.hue, self.saturation, self.value = colorsys.rgb_to_hsv(r, g, b)

        # Custom brightness bar (not pygame_gui's UIHorizontalSlider) so we
        # can recolor its background to the current hue/saturation and draw
        # our own big marker — much clearer than a plain grey slider track.
        bar_y = self.wheel_rect.bottom + margin
        self.brightness_rect = pygame.Rect(
            margin, bar_y, content_width - margin * 2, bar_height
        )
        self.brightness_image = pygame_gui.elements.UIImage(
            relative_rect=self.brightness_rect,
            image_surface=pygame.Surface(self.brightness_rect.size),
            manager=manager,
            container=container,
        )

        done_y = self.brightness_rect.bottom + margin
        done_rect = pygame.Rect(margin, done_y, content_width - margin * 2, done_height)
        self.done_button = pygame_gui.elements.UIButton(
            relative_rect=done_rect,
            text="Done",
            manager=manager,
            container=container,
        )

        self._refresh_wheel_marker()
        self._refresh_brightness_bar()

    # -----------------------------------------------------------------
    # Colour helpers
    # -----------------------------------------------------------------

    def _colour_from_state(self):
        r, g, b = colorsys.hsv_to_rgb(self.hue, self.saturation, self.value)
        return pygame.Color(int(r * 255), int(g * 255), int(b * 255))

    def _notify_colour_changed(self):
        self._refresh_wheel_marker()
        self._refresh_brightness_bar()
        self.on_colour_changed(self._colour_from_state())

    # -----------------------------------------------------------------
    # Wheel: picking + drawing the selection marker
    # -----------------------------------------------------------------

    def _pick_from_wheel(self, screen_pos):
        wheel_abs_rect = self.wheel_image.get_abs_rect()
        center_x = wheel_abs_rect.centerx
        center_y = wheel_abs_rect.centery

        dx = screen_pos[0] - center_x
        dy = screen_pos[1] - center_y
        dist = math.hypot(dx, dy)

        # Clamp rather than reject — an imprecise pointer landing just
        # outside the circle should still register as "fully saturated"
        # at that hue, not silently fail.
        self.saturation = min(dist / self.wheel_radius, 1.0)
        angle = math.degrees(math.atan2(-dy, dx)) % 360
        self.hue = angle / 360.0

        self._notify_colour_changed()

    def _refresh_wheel_marker(self):
        surface = self._base_wheel_surface.copy()

        angle_rad = math.radians(self.hue * 360)
        r = self.saturation * self.wheel_radius
        marker_x = self.wheel_radius + r * math.cos(angle_rad)
        marker_y = self.wheel_radius - r * math.sin(angle_rad)
        marker_pos = (int(marker_x), int(marker_y))

        pygame.draw.circle(surface, (0, 0, 0), marker_pos, 12, width=4)
        pygame.draw.circle(surface, (255, 255, 255), marker_pos, 9, width=3)

        self.wheel_image.set_image(surface)

    # -----------------------------------------------------------------
    # Brightness bar: a hue/saturation-tinted gradient with its own marker
    # -----------------------------------------------------------------

    def _refresh_brightness_bar(self):
        width, height = self.brightness_rect.size
        top_r, top_g, top_b = colorsys.hsv_to_rgb(self.hue, self.saturation, 1.0)
        top_color = (top_r * 255, top_g * 255, top_b * 255)

        surface = pygame.Surface((width, height))
        for x in range(width):
            t = x / max(width - 1, 1)
            surface.fill(
                (int(top_color[0] * t), int(top_color[1] * t), int(top_color[2] * t)),
                pygame.Rect(x, 0, 1, height),
            )

        marker_x = int(self.value * (width - 1))
        pygame.draw.line(surface, (0, 0, 0), (marker_x, 0), (marker_x, height), 5)
        pygame.draw.line(surface, (255, 255, 255), (marker_x, 0), (marker_x, height), 2)

        self.brightness_image.set_image(surface)

    def _pick_from_brightness_bar(self, screen_pos):
        bar_abs_rect = self.brightness_image.get_abs_rect()
        t = (screen_pos[0] - bar_abs_rect.left) / bar_abs_rect.width
        self.value = min(max(t, 0.0), 1.0)
        self._notify_colour_changed()

    # -----------------------------------------------------------------
    # Events
    # -----------------------------------------------------------------

    def process_event(self, event):
        consumed = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.wheel_image.get_abs_rect().collidepoint(event.pos):
                self.dragging_wheel = True
                self._pick_from_wheel(event.pos)
                consumed = True
            elif self.brightness_image.get_abs_rect().collidepoint(event.pos):
                self.dragging_brightness = True
                self._pick_from_brightness_bar(event.pos)
                consumed = True

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_wheel:
                self._pick_from_wheel(event.pos)
                consumed = True
            elif self.dragging_brightness:
                self._pick_from_brightness_bar(event.pos)
                consumed = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_wheel or self.dragging_brightness:
                self.dragging_wheel = False
                self.dragging_brightness = False
                consumed = True

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.done_button:
                self.on_close_callback()
                self.kill()
                return True

        if consumed:
            return True

        return super().process_event(event)
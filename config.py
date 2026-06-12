"""Cấu hình dùng chung cho Digital Twin Smart Parking."""

from __future__ import annotations

WIDTH, HEIGHT = 1600, 960
SIDEBAR_W = 390
FPS = 60
METERS_PER_PIXEL = 0.12

LANE_Y = (170.0, 330.0, 490.0, 650.0, 810.0)
SLOT_X = tuple(560.0 + index * 94.0 for index in range(10))
ENTRY = (410.0, 925.0)
ENTRY_AXIS_X = 465.0
EXIT_AXIS_X = 1530.0
EXIT_POINT = (1620.0, 925.0)
ELEVATOR = (415.0, 55.0)

COLORS = {
    "background": (9, 14, 24),
    "panel": (16, 24, 38),
    "card": (23, 34, 51),
    "card_alt": (28, 41, 59),
    "asphalt": (39, 48, 59),
    "road": (51, 61, 73),
    "road_line": (126, 139, 152),
    "white": (240, 245, 250),
    "muted": (148, 163, 181),
    "green": (42, 201, 126),
    "red": (242, 83, 91),
    "yellow": (255, 196, 61),
    "blue": (58, 154, 255),
    "cyan": (41, 211, 218),
    "orange": (255, 149, 63),
    "purple": (156, 113, 255),
    "black": (8, 12, 18),
}


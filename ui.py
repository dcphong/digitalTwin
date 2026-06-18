"""Giao diện dashboard Pygame cho Digital Twin Smart Parking."""

from __future__ import annotations

import math
import time
from pathlib import Path

import pygame
import qrcode

from config import (
    COLORS,
    ELEVATOR,
    ENTRY_AXIS_X,
    EXIT_AXIS_X,
    FPS,
    HEIGHT,
    LANE_Y,
    SIDEBAR_W,
    WIDTH,
)
from models import Car
from simulation import DigitalTwin


class Dashboard:
    def __init__(self, twin: DigitalTwin, url: str, smoke_test: bool = False) -> None:
        pygame.init()
        pygame.display.set_caption("Digital Twin Smart Parking - Tầng B1")
        flags = 0 if smoke_test else pygame.RESIZABLE
        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT) if smoke_test else self.initial_window_size(),
            flags,
        )
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.twin = twin
        self.url = url
        self.smoke_test = smoke_test
        self.show_graph = False
        self.frames = 0
        self.billing_rect = pygame.Rect(22, 618, 346, 218)
        self.billing_scroll = 0

        regular, semibold, bold = self._font_paths()
        self.fonts = {
            "xs": pygame.font.Font(regular, 12),
            "sm": pygame.font.Font(regular, 14),
            "body": pygame.font.Font(regular, 16),
            "medium": pygame.font.Font(semibold, 17),
            "title": pygame.font.Font(bold, 27),
            "number": pygame.font.Font(bold, 31),
        }
        self.qr_surface = self._make_qr(url)
        self.button_empty = pygame.Rect(22, 365, 346, 48)
        self.button_mycar = pygame.Rect(22, 421, 346, 48)
        self.speed_buttons = [
            (speed, pygame.Rect(36 + index * 62, 908, 55, 25))
            for index, speed in enumerate((0.5, 1.0, 2.0, 4.0, 8.0))
        ]

    @staticmethod
    def initial_window_size() -> tuple[int, int]:
        display = pygame.display.Info()
        max_w = max(640, int(display.current_w * 0.94))
        max_h = max(480, int(display.current_h * 0.88))
        scale = min(max_w / WIDTH, max_h / HEIGHT, 1.0)
        return max(640, int(WIDTH * scale)), max(480, int(HEIGHT * scale))

    def viewport(self) -> tuple[pygame.Rect, float]:
        sw, sh = self.screen.get_size()
        scale = min(sw / WIDTH, sh / HEIGHT)
        view_w = max(1, int(WIDTH * scale))
        view_h = max(1, int(HEIGHT * scale))
        rect = pygame.Rect((sw - view_w) // 2, (sh - view_h) // 2, view_w, view_h)
        return rect, scale

    @staticmethod
    def _font_paths() -> tuple[str | None, str | None, str | None]:
        candidates = [
            (
                Path("C:/Windows/Fonts/segoeui.ttf"),
                Path("C:/Windows/Fonts/seguisb.ttf"),
                Path("C:/Windows/Fonts/segoeuib.ttf"),
            ),
            (
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            ),
            (
                Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
                Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
                Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            ),
        ]
        for regular, semibold, bold in candidates:
            if regular.exists() and bold.exists():
                return str(regular), str(semibold if semibold.exists() else bold), str(bold)
        return None, None, None

    @staticmethod
    def _make_qr(url: str) -> pygame.Surface:
        qr = qrcode.QRCode(version=None, box_size=5, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        image = qr.make_image(fill_color="#07101c", back_color="white").convert("RGB")
        image = image.resize((132, 132))
        return pygame.image.frombytes(image.tobytes(), image.size, "RGB")

    @staticmethod
    def format_duration(minutes: float) -> str:
        total = max(0, int(minutes + 0.5))
        hours, mins = divmod(total, 60)
        if hours:
            return f"{hours}h {mins:02d}m"
        return f"{mins}m"

    @staticmethod
    def format_vnd(value: int) -> str:
        if value <= 0:
            return "0 VND"
        return f"{value:,}".replace(",", ".") + " VND"

    @staticmethod
    def rounded_polyline(
        points: list[tuple[int, int]],
        radius: float = 28.0,
        steps: int = 7,
    ) -> list[tuple[int, int]]:
        if len(points) < 3:
            return points
        rounded: list[tuple[float, float]] = [points[0]]
        for index in range(1, len(points) - 1):
            prev = points[index - 1]
            current = points[index]
            nxt = points[index + 1]
            in_dx, in_dy = current[0] - prev[0], current[1] - prev[1]
            out_dx, out_dy = nxt[0] - current[0], nxt[1] - current[1]
            in_len = math.hypot(in_dx, in_dy)
            out_len = math.hypot(out_dx, out_dy)
            if in_len < 1 or out_len < 1:
                continue
            cross = in_dx * out_dy - in_dy * out_dx
            if abs(cross) < 0.01:
                rounded.append(current)
                continue
            turn_radius = min(radius, in_len * 0.42, out_len * 0.42)
            p1 = (
                current[0] - in_dx / in_len * turn_radius,
                current[1] - in_dy / in_len * turn_radius,
            )
            p2 = (
                current[0] + out_dx / out_len * turn_radius,
                current[1] + out_dy / out_len * turn_radius,
            )
            rounded.append(p1)
            for step in range(1, steps + 1):
                t = step / steps
                inv = 1.0 - t
                rounded.append(
                    (
                        inv * inv * p1[0] + 2 * inv * t * current[0] + t * t * p2[0],
                        inv * inv * p1[1] + 2 * inv * t * current[1] + t * t * p2[1],
                    )
                )
        rounded.append(points[-1])
        return [(round(x), round(y)) for x, y in rounded]

    def text(
        self,
        value: object,
        pos: tuple[float, float],
        color: tuple[int, int, int] | None = None,
        style: str = "body",
        center: bool = False,
        right: bool = False,
        max_width: int | None = None,
    ) -> pygame.Rect:
        content = str(value)
        font = self.fonts[style]
        if max_width:
            while len(content) > 3 and font.size(content + "…")[0] > max_width:
                content = content[:-1]
            if content != str(value):
                content += "…"
        rendered = font.render(content, True, color or COLORS["white"])
        rect = rendered.get_rect()
        if center:
            rect.center = pos
        elif right:
            rect.topright = pos
        else:
            rect.topleft = pos
        self.canvas.blit(rendered, rect)
        return rect

    def card(
        self,
        rect: pygame.Rect,
        color: tuple[int, int, int] | None = None,
        radius: int = 15,
        border: bool = True,
    ) -> None:
        pygame.draw.rect(self.canvas, (5, 9, 16), rect.move(0, 5), border_radius=radius)
        pygame.draw.rect(self.canvas, color or COLORS["card"], rect, border_radius=radius)
        if border:
            pygame.draw.rect(self.canvas, (39, 55, 75), rect, 1, border_radius=radius)

    def draw_sidebar(self) -> None:
        pygame.draw.rect(self.canvas, COLORS["panel"], (0, 0, SIDEBAR_W, HEIGHT))
        pygame.draw.line(
            self.canvas, (37, 51, 69), (SIDEBAR_W - 1, 0), (SIDEBAR_W - 1, HEIGHT)
        )

        self.text("MALL DIGITAL TWIN", (22, 18), COLORS["cyan"], "xs")
        self.text("Smart Parking B1", (22, 37), style="title")
        self.text("Trung tâm điều hành thời gian thực", (22, 69), COLORS["muted"], "sm")

        self.card(pygame.Rect(22, 96, 346, 166))
        pygame.draw.rect(self.canvas, COLORS["white"], (34, 111, 142, 142), border_radius=10)
        self.canvas.blit(self.qr_surface, (39, 116))
        self.text("QUÉT MÃ ĐỂ TRUY CẬP", (193, 117), COLORS["blue"], "xs")
        self.text("Giao diện khách hàng", (193, 140), style="medium")
        self.text("Điện thoại và máy tính", (193, 169), COLORS["muted"], "sm")
        self.text("dùng chung mạng Wi-Fi", (193, 190), COLORS["muted"], "sm")
        self.text(self.url, (193, 224), COLORS["cyan"], "xs", max_width=160)

        snapshot = self.twin.bridge.get_snapshot()
        stats = [
            ("TRỐNG", snapshot.get("free", 0), COLORS["green"]),
            ("ĐÃ ĐỖ", snapshot.get("occupied", 0), COLORS["red"]),
            ("ĐANG ĐI", snapshot.get("moving", 0), COLORS["blue"]),
        ]
        for index, (label, value, color) in enumerate(stats):
            rect = pygame.Rect(22 + index * 117, 277, 108, 73)
            self.card(rect, COLORS["card_alt"], 12)
            self.text(value, (rect.centerx, rect.y + 25), color, "number", center=True)
            self.text(label, (rect.centerx, rect.y + 57), COLORS["muted"], "xs", center=True)

        self.draw_button(
            self.button_empty,
            "TẮT HƯỚNG DẪN CHỖ ĐỖ"
            if self.twin.guide_mode == "empty"
            else "TÌM CHỖ ĐỖ TỐT NHẤT",
            COLORS["blue"],
            self.twin.guide_mode == "empty",
        )
        self.draw_button(
            self.button_mycar,
            "TẮT HƯỚNG DẪN TÌM XE"
            if self.twin.guide_mode == "mycar"
            else "DẪN ĐẾN XE CỦA TÔI",
            COLORS["yellow"],
            self.twin.guide_mode == "mycar",
            dark_text=True,
        )

        self.card(pygame.Rect(22, 485, 346, 118))
        self.text("ĐIỀU HƯỚNG A*", (36, 499), COLORS["cyan"], "xs")
        self.text(
            self.twin.message,
            (36, 520),
            COLORS["white"],
            "sm",
            max_width=315,
        )
        route_items = [
            ("ĐÍCH", self.twin.guide_target or "--"),
            ("QUÃNG ĐƯỜNG", f"{self.twin.guide_distance:.0f} m" if self.twin.guide_path else "--"),
            ("NODE ĐÃ DUYỆT", self.twin.guide_expanded or "--"),
        ]
        for index, (label, value) in enumerate(route_items):
            x = 36 + index * 106
            self.text(value, (x, 554), COLORS["white"], "medium")
            self.text(label, (x, 579), COLORS["muted"], "xs")

        self.draw_billing_card(self.billing_rect)

        self.card(pygame.Rect(22, 850, 346, 88))
        self.text("CHÚ GIẢI & ĐIỀU KHIỂN", (36, 862), COLORS["white"], "medium")
        legends = [
            (COLORS["green"], "Trống"),
            (COLORS["red"], "Đã đỗ"),
            (COLORS["blue"], "Đã giữ"),
            (COLORS["yellow"], "Xe của bạn"),
        ]
        for index, (color, label) in enumerate(legends):
            x = 36 + (index % 2) * 150
            y = 889 + (index // 2) * 19
            pygame.draw.rect(self.canvas, color, (x, y, 13, 13), border_radius=3)
            self.text(label, (x + 21, y - 2), COLORS["muted"], "xs")
        for speed, rect in self.speed_buttons:
            active = self.twin.speed_multiplier == speed
            hover = rect.collidepoint(self.logical_mouse())
            fill = COLORS["cyan"] if active else (45, 59, 76) if hover else (32, 45, 61)
            text_color = COLORS["black"] if active else COLORS["white"]
            pygame.draw.rect(self.canvas, fill, rect, border_radius=6)
            pygame.draw.rect(
                self.canvas,
                COLORS["white"] if active else (70, 86, 105),
                rect,
                1,
                border_radius=6,
            )
            self.text(f"{speed:g}x", rect.center, text_color, "xs", center=True)

    def draw_billing_card(self, rect: pygame.Rect) -> None:
        self.card(rect, (22, 35, 52), 15)
        self.text("BẢNG TÍNH PHÍ ĐỖ XE", (rect.x + 14, rect.y + 14), COLORS["white"], "medium")
        self.text(
            "Miễn phí 10p • 10.000 VND/30p đầu • +5.000 VND/30p",
            (rect.x + 14, rect.y + 38),
            COLORS["muted"],
            "xs",
            max_width=232,
        )

        header_y = rect.y + 64
        self.text("BIỂN SỐ", (rect.x + 14, header_y), COLORS["cyan"], "xs")
        self.text("Ô", (rect.x + 134, header_y), COLORS["cyan"], "xs")
        self.text("TG", (rect.x + 205, header_y), COLORS["cyan"], "xs")
        self.text("PHÍ", (rect.right - 14, header_y), COLORS["cyan"], "xs", right=True)
        pygame.draw.line(
            self.canvas,
            (45, 63, 83),
            (rect.x + 14, header_y + 19),
            (rect.right - 14, header_y + 19),
            1,
        )

        visible_count = 6
        rows = self.twin.billing_rows(100)
        max_scroll = max(0, len(rows) - visible_count)
        self.billing_scroll = max(0, min(self.billing_scroll, max_scroll))
        visible_rows = rows[self.billing_scroll:self.billing_scroll + visible_count]
        row_y = header_y + 29
        if not rows:
            self.text("Chưa có xe đang đỗ.", (rect.x + 14, row_y), COLORS["muted"], "sm")
            return
        for index, row in enumerate(visible_rows):
            y = row_y + index * 22
            mine = bool(row["mine"])
            if mine:
                highlight = pygame.Rect(rect.x + 9, y - 4, rect.w - 27, 20)
                pygame.draw.rect(self.canvas, (60, 46, 16), highlight, border_radius=7)
                pygame.draw.rect(self.canvas, COLORS["yellow"], highlight, 1, border_radius=7)
            color = COLORS["yellow"] if mine else COLORS["white"]
            self.text(row["plate"], (rect.x + 14, y), color, "xs", max_width=116)
            self.text(row["slot"], (rect.x + 134, y), COLORS["white"], "xs", max_width=60)
            self.text(
                self.format_duration(float(row["minutes"])),
                (rect.x + 205, y),
                COLORS["white"],
                "xs",
                max_width=54,
            )
            self.text(
                self.format_vnd(int(row["fee_vnd"])),
                (rect.right - 14, y),
                COLORS["green"] if int(row["fee_vnd"]) else COLORS["muted"],
                "xs",
                right=True,
                max_width=82,
            )
        if max_scroll:
            track = pygame.Rect(rect.right - 10, row_y - 2, 4, visible_count * 22 + 2)
            thumb_h = max(18, int(track.h * visible_count / len(rows)))
            thumb_y = track.y + int((track.h - thumb_h) * self.billing_scroll / max_scroll)
            pygame.draw.rect(self.canvas, (42, 57, 76), track, border_radius=2)
            pygame.draw.rect(
                self.canvas,
                COLORS["cyan"],
                (track.x, thumb_y, track.w, thumb_h),
                border_radius=2,
            )
            self.text(
                f"{self.billing_scroll + 1}-{self.billing_scroll + len(visible_rows)}/{len(rows)}",
                (rect.right - 14, rect.y + 38),
                COLORS["cyan"],
                "xs",
                right=True,
            )

    def draw_button(
        self,
        rect: pygame.Rect,
        label: str,
        color: tuple[int, int, int],
        active: bool,
        dark_text: bool = False,
    ) -> None:
        hover = rect.collidepoint(self.logical_mouse())
        fill = tuple(min(255, channel + (15 if hover else 0)) for channel in color)
        pygame.draw.rect(self.canvas, fill, rect, border_radius=12)
        if active:
            pygame.draw.rect(self.canvas, COLORS["white"], rect, 2, border_radius=12)
        text_color = COLORS["black"] if dark_text else COLORS["white"]
        self.text(label, rect.center, text_color, "medium", center=True)

    def draw_lot(self) -> None:
        pygame.draw.rect(
            self.canvas,
            COLORS["asphalt"],
            (SIDEBAR_W, 0, WIDTH - SIDEBAR_W, HEIGHT),
        )
        self.draw_header()
        self.draw_roads()
        if self.show_graph:
            self.draw_graph()
        self.draw_slots()
        self.draw_infrastructure()
        self.draw_guidance()
        for car in self.twin.cars:
            self.draw_car(car)
        self.draw_event_bar()

    def draw_header(self) -> None:
        self.card(pygame.Rect(412, 17, 1166, 61), (19, 28, 42), 14)
        self.text("SƠ ĐỒ VẬN HÀNH • 100 VỊ TRÍ ĐỖ XE", (432, 29), style="medium")
        self.text(
            f"Đội xe mô phỏng: {len(self.twin.cars)}",
            (432, 52),
            COLORS["muted"],
            "xs",
        )
        status = "TẠM DỪNG" if self.twin.paused else "ĐANG HOẠT ĐỘNG"
        status_color = COLORS["orange"] if self.twin.paused else COLORS["green"]
        pygame.draw.circle(self.canvas, status_color, (1392, 47), 6)
        self.text(status, (1406, 36), status_color, "sm")
        self.text(
            f"x{self.twin.speed_multiplier:g}",
            (1554, 36),
            COLORS["cyan"],
            "medium",
            right=True,
        )

    def draw_roads(self) -> None:
        curb = (30, 39, 50)
        lane_shadow = (26, 34, 44)
        for lane_y in LANE_Y:
            pygame.draw.rect(
                self.canvas,
                curb,
                (ENTRY_AXIS_X - 10, lane_y - 31, EXIT_AXIS_X - ENTRY_AXIS_X + 20, 62),
                border_radius=18,
            )
            pygame.draw.rect(
                self.canvas,
                COLORS["road"],
                (ENTRY_AXIS_X, lane_y - 23, EXIT_AXIS_X - ENTRY_AXIS_X, 46),
                border_radius=14,
            )
            for x in range(510, 1490, 74):
                pygame.draw.line(
                    self.canvas,
                    COLORS["road_line"],
                    (x, lane_y),
                    (x + 34, lane_y),
                    2,
                )
            for x in range(590, 1470, 170):
                pygame.draw.lines(
                    self.canvas,
                    COLORS["road_line"],
                    False,
                    [(x - 9, lane_y - 6), (x + 2, lane_y), (x - 9, lane_y + 6)],
                    2,
                )
            for axis_x in (ENTRY_AXIS_X, EXIT_AXIS_X):
                pygame.draw.circle(self.canvas, curb, (round(axis_x), round(lane_y)), 31)
                pygame.draw.circle(self.canvas, COLORS["road"], (round(axis_x), round(lane_y)), 23)

        pygame.draw.rect(self.canvas, curb, (434, 83, 62, 843), border_radius=20)
        pygame.draw.rect(self.canvas, curb, (1499, 83, 62, 843), border_radius=20)
        pygame.draw.rect(self.canvas, COLORS["road"], (442, 83, 46, 843), border_radius=16)
        pygame.draw.rect(self.canvas, COLORS["road"], (1507, 83, 46, 843), border_radius=16)
        pygame.draw.rect(self.canvas, lane_shadow, (390, 894, 1210, 64), border_radius=20)
        pygame.draw.rect(self.canvas, COLORS["road"], (390, 902, 1210, 48), border_radius=16)
        for y in range(130, 890, 115):
            pygame.draw.lines(
                self.canvas,
                COLORS["road_line"],
                False,
                [(458, y + 8), (465, y - 3), (472, y + 8)],
                2,
            )
            pygame.draw.lines(
                self.canvas,
                COLORS["road_line"],
                False,
                [(1523, y - 8), (1530, y + 3), (1537, y - 8)],
                2,
            )
        for x in range(470, 1540, 105):
            pygame.draw.line(
                self.canvas,
                COLORS["road_line"],
                (x, 926),
                (x + 42, 926),
                2,
            )

    def draw_slots(self) -> None:
        customer_slot = next(
            (
                car.slot_id
                for car in self.twin.cars
                if car.car_id == self.twin.customer_car_id
            ),
            None,
        )
        for slot in self.twin.slots:
            mine = slot.slot_id == customer_slot and slot.occupied_by is not None
            color = (
                COLORS["yellow"]
                if mine
                else COLORS["red"]
                if slot.occupied_by is not None
                else COLORS["blue"]
                if slot.reserved_by is not None
                else COLORS["green"]
            )
            rect = pygame.Rect(0, 0, 72, 36)
            rect.center = (round(slot.x), round(slot.y))
            pygame.draw.rect(self.canvas, (17, 23, 31), rect.inflate(4, 4), border_radius=7)
            pygame.draw.rect(self.canvas, color, rect, border_radius=6)
            pygame.draw.rect(self.canvas, (255, 255, 255), rect, 1, border_radius=6)
            if slot.electric:
                pygame.draw.rect(self.canvas, COLORS["cyan"], rect.inflate(5, 5), 2, border_radius=8)
            text_color = COLORS["black"] if mine or slot.occupied_by is None else COLORS["white"]
            self.text(slot.slot_id, rect.center, text_color, "xs", center=True)
            if slot.electric:
                self.draw_ev_icon((rect.right - 11, rect.top + 11))
            if slot.accessible:
                pygame.draw.circle(self.canvas, COLORS["white"], (rect.left + 6, rect.top + 6), 4, 1)
        for index, lane_y in enumerate(LANE_Y):
            self.text(
                f"KHU {chr(65 + index)}",
                (500, lane_y),
                COLORS["muted"],
                "xs",
                center=True,
            )

    def draw_ev_icon(self, center: tuple[int, int]) -> None:
        """Draw a high-contrast charging badge instead of an ambiguous dot."""
        x, y = center
        pygame.draw.circle(self.canvas, (4, 16, 24), (x, y), 11)
        pygame.draw.circle(self.canvas, COLORS["cyan"], (x, y), 11, 2)
        bolt = [
            (x + 2, y - 8),
            (x - 5, y + 1),
            (x, y + 1),
            (x - 2, y + 9),
            (x + 7, y - 2),
            (x + 2, y - 2),
        ]
        pygame.draw.polygon(self.canvas, COLORS["yellow"], bolt)

    def draw_infrastructure(self) -> None:
        self.card(pygame.Rect(398, 88, 58, 58), (28, 42, 57), 10)
        self.text("LIFT", (427, 111), COLORS["cyan"], "xs", center=True)
        self.text("SẢNH", (427, 129), COLORS["muted"], "xs", center=True)

        self.draw_barrier((425, 902), self.twin.entry_barrier_open, "CỔNG VÀO")
        self.draw_barrier((1530, 902), self.twin.exit_barrier_open, "LỐI RA")
        self.draw_camera((493, 891), "ANPR")
        self.draw_camera((1470, 891), "ANPR")

        for x in (720, 1080, 1400):
            self.draw_camera((x, 96), "AI")
        self.text("EV", (1367, 101), COLORS["cyan"], "xs")
        self.text("10 trạm sạc", (1390, 101), COLORS["muted"], "xs")

    def draw_barrier(self, point: tuple[int, int], opened: bool, label: str) -> None:
        x, y = point
        pygame.draw.rect(self.canvas, COLORS["orange"], (x - 8, y - 10, 16, 24), border_radius=4)
        end = (x + 35, y - 28) if opened else (x + 45, y)
        pygame.draw.line(self.canvas, COLORS["white"], (x, y - 7), end, 5)
        self.text(label, (x, y + 18), COLORS["white"], "xs", center=True)

    def draw_camera(self, point: tuple[int, int], label: str) -> None:
        x, y = point
        pygame.draw.rect(self.canvas, COLORS["card_alt"], (x - 13, y - 8, 26, 16), border_radius=4)
        pygame.draw.circle(self.canvas, COLORS["cyan"], (x + 5, y), 4)
        pygame.draw.line(self.canvas, COLORS["muted"], (x - 3, y + 8), (x - 3, y + 17), 2)
        self.text(label, (x, y + 24), COLORS["muted"], "xs", center=True)

    def draw_graph(self) -> None:
        drawn: set[frozenset[tuple[float, float]]] = set()
        for node, neighbors in self.twin.graph.edges.items():
            for neighbor in neighbors:
                edge = frozenset((node, neighbor))
                if edge in drawn:
                    continue
                drawn.add(edge)
                pygame.draw.line(self.canvas, (49, 130, 174), node, neighbor, 1)
        for node in self.twin.graph.edges:
            pygame.draw.circle(self.canvas, COLORS["cyan"], node, 3)

    def draw_guidance(self) -> None:
        path = self.twin.guide_path
        if len(path) < 2:
            return
        color = COLORS["yellow"] if self.twin.guide_mode == "mycar" else COLORS["blue"]
        if self.twin.guide_mode == "empty" and self.twin.guide_target:
            slot = self.twin.slot_by_id.get(self.twin.guide_target)
            if slot:
                path = self.twin.entry_route_points(slot)
        points = self.rounded_polyline([(round(x), round(y)) for x, y in path], radius=36.0, steps=9)
        pygame.draw.lines(self.canvas, COLORS["black"], False, points, 11)
        pygame.draw.lines(self.canvas, color, False, points, 5)
        spacing = 42
        remaining = (time.monotonic() * 95) % spacing
        for first, second in zip(points, points[1:]):
            length = math.dist(first, second)
            if length < 1:
                continue
            ux = (second[0] - first[0]) / length
            uy = (second[1] - first[1]) / length
            marker = remaining
            while marker < length:
                pygame.draw.circle(
                    self.canvas,
                    COLORS["white"],
                    (round(first[0] + ux * marker), round(first[1] + uy * marker)),
                    3,
                )
                marker += spacing
            remaining = marker - length
        first, second = points[-2], points[-1]
        length = math.dist(first, second)
        if length >= 1:
            ux = (second[0] - first[0]) / length
            uy = (second[1] - first[1]) / length
            wing = 10
            pygame.draw.polygon(
                self.canvas,
                color,
                [
                    second,
                    (
                        round(second[0] - ux * 18 - uy * wing),
                        round(second[1] - uy * 18 + ux * wing),
                    ),
                    (
                        round(second[0] - ux * 18 + uy * wing),
                        round(second[1] - uy * 18 - ux * wing),
                    ),
                ],
            )
        pulse = 13 + int(4 * math.sin(time.monotonic() * 5))
        pygame.draw.circle(self.canvas, color, points[-1], pulse, 3)

    def draw_car(self, car: Car) -> None:
        if car.state not in {"entering", "leaving"}:
            return
        body = pygame.Surface((42, 22), pygame.SRCALPHA)
        pygame.draw.rect(body, (4, 7, 11, 90), (2, 4, 38, 18), border_radius=7)
        pygame.draw.rect(body, car.color, (1, 2, 40, 17), border_radius=7)
        pygame.draw.rect(body, (174, 219, 238), (10, 4, 17, 12), border_radius=3)
        for x in (6, 29):
            pygame.draw.rect(body, COLORS["black"], (x, 0, 8, 4), border_radius=2)
            pygame.draw.rect(body, COLORS["black"], (x, 17, 8, 4), border_radius=2)
        rotated = pygame.transform.rotate(body, car.angle)
        self.canvas.blit(rotated, rotated.get_rect(center=(round(car.x), round(car.y))))

    def draw_event_bar(self) -> None:
        rect = pygame.Rect(780, 49, 590, 25)
        pygame.draw.rect(self.canvas, (12, 19, 29, 225), rect, border_radius=10)
        pygame.draw.circle(self.canvas, COLORS["green"], (rect.x + 16, rect.centery), 5)
        self.text(
            self.twin.last_event,
            (rect.x + 29, rect.y + 5),
            COLORS["white"],
            "sm",
            max_width=540,
        )

    def logical_mouse(self) -> tuple[int, int]:
        mx, my = pygame.mouse.get_pos()
        rect, scale = self.viewport()
        if not rect.collidepoint(mx, my):
            return -1, -1
        return int((mx - rect.x) / scale), int((my - rect.y) / scale)

    def process_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_1, pygame.K_KP1):
                    self.twin.handle_action("empty")
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self.twin.handle_action("mycar")
                elif event.key == pygame.K_SPACE:
                    self.twin.paused = not self.twin.paused
                elif event.key == pygame.K_g:
                    self.show_graph = not self.show_graph
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    self.twin.speed_multiplier = min(8, self.twin.speed_multiplier * 2)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.twin.speed_multiplier = max(0.5, self.twin.speed_multiplier / 2)
                elif event.key in (
                    pygame.K_3,
                    pygame.K_4,
                    pygame.K_5,
                    pygame.K_6,
                    pygame.K_7,
                ):
                    speed_index = event.key - pygame.K_3
                    self.twin.speed_multiplier = (0.5, 1.0, 2.0, 4.0, 8.0)[speed_index]
                elif event.key == pygame.K_r:
                    count = len(self.twin.cars)
                    bridge = self.twin.bridge
                    self.twin.__init__(count, bridge, seed=int(time.time()))
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                point = self.logical_mouse()
                if self.button_empty.collidepoint(point):
                    self.twin.handle_action("empty")
                elif self.button_mycar.collidepoint(point):
                    self.twin.handle_action("mycar")
                else:
                    for speed, rect in self.speed_buttons:
                        if rect.collidepoint(point):
                            self.twin.speed_multiplier = speed
                            break
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
                point = self.logical_mouse()
                if self.billing_rect.collidepoint(point):
                    rows = self.twin.billing_rows(100)
                    max_scroll = max(0, len(rows) - 6)
                    delta = -1 if event.button == 4 else 1
                    self.billing_scroll = max(0, min(max_scroll, self.billing_scroll + delta))
            if event.type == pygame.MOUSEWHEEL:
                point = self.logical_mouse()
                if self.billing_rect.collidepoint(point):
                    rows = self.twin.billing_rows(100)
                    max_scroll = max(0, len(rows) - 6)
                    self.billing_scroll = max(
                        0,
                        min(max_scroll, self.billing_scroll - event.y),
                    )
        return True

    def draw(self) -> None:
        self.canvas.fill(COLORS["background"])
        self.draw_lot()
        self.draw_sidebar()
        rect, _scale = self.viewport()
        self.screen.fill(COLORS["background"])
        if rect.size == (WIDTH, HEIGHT):
            self.screen.blit(self.canvas, (0, 0))
        else:
            self.screen.blit(
                pygame.transform.smoothscale(self.canvas, rect.size),
                rect,
            )
        pygame.display.flip()

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.process_events()
            self.twin.update(dt)
            self.draw()
            self.frames += 1
            if self.smoke_test and self.frames >= 180:
                running = False
        pygame.quit()

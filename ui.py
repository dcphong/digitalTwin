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
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.twin = twin
        self.url = url
        self.smoke_test = smoke_test
        self.show_graph = False
        self.frames = 0

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
            "TÌM CHỖ ĐỖ TỐT NHẤT",
            COLORS["blue"],
            self.twin.guide_mode == "empty",
        )
        self.draw_button(
            self.button_mycar,
            "DẪN ĐẾN XE CỦA TÔI",
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

        self.card(pygame.Rect(22, 618, 346, 178))
        self.text("HẠ TẦNG BÃI XE HIỆN ĐẠI", (36, 632), COLORS["white"], "medium")
        technologies = [
            ("ANPR / Biển số", snapshot.get("last_plate", "---"), COLORS["purple"]),
            ("Cảm biến IoT", f"{snapshot.get('sensor_uptime', 0)}%", COLORS["green"]),
            ("Độ trễ dữ liệu", f"{snapshot.get('iot_latency', 0)} ms", COLORS["cyan"]),
            ("Trạm sạc EV", "10 vị trí", COLORS["blue"]),
            ("Thanh toán số", "Sẵn sàng", COLORS["yellow"]),
            ("Barrier tự động", "Đang kết nối", COLORS["orange"]),
        ]
        for index, (label, value, color) in enumerate(technologies):
            column, row = index % 2, index // 2
            x, y = 36 + column * 164, 667 + row * 39
            pygame.draw.circle(self.canvas, color, (x + 5, y + 7), 5)
            self.text(label, (x + 16, y - 2), COLORS["muted"], "xs")
            self.text(value, (x + 16, y + 14), COLORS["white"], "sm", max_width=135)

        self.card(pygame.Rect(22, 811, 346, 126))
        self.text("CHÚ GIẢI & ĐIỀU KHIỂN", (36, 825), COLORS["white"], "medium")
        legends = [
            (COLORS["green"], "Trống"),
            (COLORS["red"], "Đã đỗ"),
            (COLORS["blue"], "Đã giữ"),
            (COLORS["yellow"], "Xe của bạn"),
        ]
        for index, (color, label) in enumerate(legends):
            x = 36 + (index % 2) * 150
            y = 856 + (index // 2) * 25
            pygame.draw.rect(self.canvas, color, (x, y, 13, 13), border_radius=3)
            self.text(label, (x + 21, y - 2), COLORS["muted"], "xs")
        self.text("1/2: dẫn đường   G: graph   +/-: tốc độ", (36, 909), COLORS["muted"], "xs")

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
        for lane_y in LANE_Y:
            pygame.draw.rect(
                self.canvas,
                COLORS["road"],
                (ENTRY_AXIS_X, lane_y - 23, EXIT_AXIS_X - ENTRY_AXIS_X, 46),
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
        pygame.draw.rect(self.canvas, COLORS["road"], (442, 83, 46, 843))
        pygame.draw.rect(self.canvas, COLORS["road"], (1507, 83, 46, 843))
        pygame.draw.rect(self.canvas, COLORS["road"], (390, 902, 1210, 48))
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
            text_color = COLORS["black"] if mine or slot.occupied_by is None else COLORS["white"]
            self.text(slot.slot_id, rect.center, text_color, "xs", center=True)
            if slot.electric:
                pygame.draw.circle(self.canvas, COLORS["cyan"], (rect.right - 5, rect.top + 5), 4)
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
        points = [(round(x), round(y)) for x, y in path]
        pygame.draw.lines(self.canvas, COLORS["black"], False, points, 11)
        pygame.draw.lines(self.canvas, color, False, points, 5)
        phase = (time.monotonic() * 90) % 40
        for first, second in zip(points, points[1:]):
            length = math.dist(first, second)
            if length < 1:
                continue
            ux = (second[0] - first[0]) / length
            uy = (second[1] - first[1]) / length
            marker = phase
            while marker < length:
                pygame.draw.circle(
                    self.canvas,
                    COLORS["white"],
                    (round(first[0] + ux * marker), round(first[1] + uy * marker)),
                    3,
                )
                marker += 40
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
        rect = pygame.Rect(645, 862, 650, 34)
        pygame.draw.rect(self.canvas, (12, 19, 29, 225), rect, border_radius=10)
        pygame.draw.circle(self.canvas, COLORS["green"], (663, 879), 5)
        self.text(
            self.twin.last_event,
            (676, 869),
            COLORS["white"],
            "sm",
            max_width=600,
        )

    def logical_mouse(self) -> tuple[int, int]:
        mx, my = pygame.mouse.get_pos()
        sw, sh = self.screen.get_size()
        return int(mx * WIDTH / max(1, sw)), int(my * HEIGHT / max(1, sh))

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
        return True

    def draw(self) -> None:
        self.canvas.fill(COLORS["background"])
        self.draw_lot()
        self.draw_sidebar()
        if self.screen.get_size() == (WIDTH, HEIGHT):
            self.screen.blit(self.canvas, (0, 0))
        else:
            self.screen.blit(
                pygame.transform.smoothscale(self.canvas, self.screen.get_size()),
                (0, 0),
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

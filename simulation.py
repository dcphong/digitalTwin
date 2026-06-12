"""Lõi Digital Twin: 100 chỗ, đội xe, cảm biến và điều phối A*."""

from __future__ import annotations

import math
import random
import time

from config import (
    ELEVATOR,
    ENTRY,
    ENTRY_AXIS_X,
    EXIT_AXIS_X,
    EXIT_POINT,
    LANE_Y,
    METERS_PER_PIXEL,
    SLOT_X,
)
from models import Car, ParkingSlot, SharedBridge
from navigation import LaneGraph, Point


class DigitalTwin:
    def __init__(self, car_count: int, bridge: SharedBridge, seed: int = 2026) -> None:
        self.rng = random.Random(seed)
        self.bridge = bridge
        self.slots = self._make_slots()
        self.slot_by_id = {slot.slot_id: slot for slot in self.slots}
        self.graph = LaneGraph(self.slots)
        self.cars = self._make_cars(car_count)

        self.elapsed = 0.0
        self.completed_trips = 0
        self.next_spawn = 0.0
        self.entry_release_at = 0.0
        self.speed_multiplier = 1.0
        self.paused = False
        self.customer_car_id: int | None = None

        self.guide_mode: str | None = None
        self.guide_target: str | None = None
        self.guide_path: list[Point] = []
        self.guide_distance = 0.0
        self.guide_expanded = 0
        self.astar_calls = 0
        self.message = "Chọn chức năng để hệ thống bắt đầu dẫn đường."

        self.entry_barrier_open = False
        self.exit_barrier_open = False
        self.last_plate = "---"
        self.last_event = "Hệ thống đã sẵn sàng"
        self.iot_latency_ms = 28
        self.sensor_uptime = 100.0
        self._populate_initial_cars()
        self.publish_snapshot()

    def _make_slots(self) -> list[ParkingSlot]:
        slots: list[ParkingSlot] = []
        zones = "ABCDE"
        for lane_index, lane_y in enumerate(LANE_Y):
            for side, offset in (("N", -49.0), ("S", 49.0)):
                for column, x in enumerate(SLOT_X, 1):
                    slot_id = f"{zones[lane_index]}{side}-{column:02d}"
                    electric = lane_index == 0 and column >= 6
                    accessible = lane_index == 0 and column <= 2
                    slots.append(
                        ParkingSlot(
                            slot_id=slot_id,
                            zone=zones[lane_index],
                            x=x,
                            y=lane_y + offset,
                            lane_y=lane_y,
                            electric=electric,
                            accessible=accessible,
                        )
                    )
        return slots

    def _make_cars(self, count: int) -> list[Car]:
        palette = [
            (62, 149, 255), (255, 112, 76), (170, 112, 255),
            (255, 194, 68), (45, 205, 187), (228, 235, 242),
            (64, 99, 157), (237, 84, 128), (121, 190, 91),
        ]
        cars = []
        for index in range(count):
            plate = f"{self.rng.randint(29, 99)}{self.rng.choice('ABCDEFGH')}-"
            plate += f"{self.rng.randint(100, 999)}.{self.rng.randint(10, 99)}"
            cars.append(
                Car(
                    car_id=index + 1,
                    plate=plate,
                    color=self.rng.choice(palette),
                    speed=self.rng.uniform(100, 138),
                )
            )
        return cars

    def _populate_initial_cars(self) -> None:
        initial_count = min(82, max(44, int(len(self.cars) * 0.62)))
        chosen_slots = self.rng.sample(self.slots, initial_count)
        for car, slot in zip(self.cars[:initial_count], chosen_slots):
            car.state = "parked"
            car.x, car.y = slot.x, slot.y
            car.slot_id = slot.slot_id
            car.parked_for = self.rng.uniform(25, 95)
            slot.occupied_by = car.car_id
        for car in self.cars[initial_count:]:
            car.wait_for = self.rng.uniform(1, 24)
        if chosen_slots:
            customer = self.cars[0]
            self.customer_car_id = customer.car_id
            customer.parked_for = 10**9

    def available_slots(self) -> list[ParkingSlot]:
        return [
            slot
            for slot in self.slots
            if slot.occupied_by is None
            and slot.reserved_by is None
            and slot.slot_id != self.guide_target
        ]

    def congestion_map(self, ignored_car: Car | None = None) -> dict[Point, float]:
        congestion: dict[Point, float] = {}
        for car in self.cars:
            if car is ignored_car or car.state not in {"entering", "leaving"}:
                continue
            nearest = min(
                self.graph.edges,
                key=lambda node: math.hypot(node[0] - car.x, node[1] - car.y),
            )
            congestion[nearest] = congestion.get(nearest, 0.0) + 0.7
        return congestion

    def find_route(
        self,
        start: Point,
        goal: Point,
        ignored_car: Car | None = None,
        blocked_nodes: set[Point] | None = None,
    ) -> tuple[list[Point], float, int]:
        self.astar_calls += 1
        return self.graph.astar(
            start,
            goal,
            self.congestion_map(ignored_car),
            blocked_nodes,
        )

    def entry_route(self, car: Car, slot: ParkingSlot) -> tuple[list[Point], float, int]:
        """Keep arriving cars on the left entry spine."""
        blocked = {
            node
            for node in self.graph.edges
            if node[0] == EXIT_AXIS_X
        }
        return self.find_route(ENTRY, (slot.x, slot.y), car, blocked)

    def exit_route(self, car: Car, slot: ParkingSlot) -> tuple[list[Point], float, int]:
        """Keep departing cars on the right exit spine, away from the entrance."""
        blocked = {
            node
            for node in self.graph.edges
            if node[0] == ENTRY_AXIS_X or node == ENTRY
        }
        return self.find_route((slot.x, slot.y), EXIT_POINT, car, blocked)

    def entry_is_clear(self) -> bool:
        """Release one car only after the previous car clears the gate corridor."""
        if self.elapsed < self.entry_release_at:
            return False
        for car in self.cars:
            if car.state not in {"entering", "leaving"}:
                continue
            if math.hypot(car.x - ENTRY[0], car.y - ENTRY[1]) < 105:
                return False
            if car.x <= ENTRY_AXIS_X + 24 and car.y >= LANE_Y[-1] - 25:
                return False
        return True

    def select_empty_guidance(self) -> None:
        candidates = self.available_slots()
        options: list[tuple[float, str, ParkingSlot, list[Point], int]] = []
        for slot in candidates:
            path, cost, expanded = self.find_route(ENTRY, (slot.x, slot.y))
            if path:
                options.append((cost, slot.slot_id, slot, path, expanded))
        if not options:
            self._clear_guidance("Bãi xe hiện không còn vị trí trống.")
            return
        cost, _, target, path, expanded = min(options)
        self.guide_mode = "empty"
        self.guide_target = target.slot_id
        self.guide_path = path
        self.guide_distance = cost * METERS_PER_PIXEL
        self.guide_expanded = expanded
        self.message = (
            f"A* đề xuất chỗ {target.slot_id}, cách cổng vào "
            f"{self.guide_distance:.0f} m."
        )

    def select_my_car_guidance(self) -> None:
        car = next((item for item in self.cars if item.car_id == self.customer_car_id), None)
        if not car or not car.slot_id:
            self._clear_guidance("Không tìm thấy vị trí xe của bạn.")
            return
        target = self.slot_by_id[car.slot_id]
        path, cost, expanded = self.find_route(ELEVATOR, (target.x, target.y))
        self.guide_mode = "mycar"
        self.guide_target = target.slot_id
        self.guide_path = path
        self.guide_distance = cost * METERS_PER_PIXEL
        self.guide_expanded = expanded
        self.message = (
            f"Xe {car.plate} ở {target.slot_id}. Tuyến đi bộ dài "
            f"{self.guide_distance:.0f} m."
        )

    def _clear_guidance(self, message: str) -> None:
        self.guide_mode = None
        self.guide_target = None
        self.guide_path = []
        self.guide_distance = 0.0
        self.guide_expanded = 0
        self.message = message

    def handle_action(self, action: str) -> None:
        if action == "empty":
            self.select_empty_guidance()
        elif action == "mycar":
            self.select_my_car_guidance()
        self.publish_snapshot()

    def start_entering(self, car: Car, slot: ParkingSlot) -> bool:
        if not self.entry_is_clear():
            return False
        route, _, _ = self.entry_route(car, slot)
        if not route:
            car.wait_for = 3.0
            return False
        car.state = "entering"
        car.slot_id = slot.slot_id
        car.x, car.y = ENTRY
        car.route = route[1:]
        car.route_index = 0
        car.distance_travelled = 0.0
        slot.reserved_by = car.car_id
        self.entry_barrier_open = True
        self.entry_release_at = self.elapsed + 1.25
        self.last_plate = car.plate
        self.last_event = f"ANPR nhận diện xe vào: {car.plate}"
        return True

    def start_leaving(self, car: Car) -> bool:
        if not car.slot_id:
            return False
        slot = self.slot_by_id[car.slot_id]
        route, _, _ = self.exit_route(car, slot)
        if not route:
            car.parked_for = 3.0
            return False
        slot.occupied_by = None
        car.state = "leaving"
        car.route = route[1:]
        car.route_index = 0
        car.distance_travelled = 0.0
        return True

    def finish_route(self, car: Car) -> None:
        if car.state == "entering" and car.slot_id:
            slot = self.slot_by_id[car.slot_id]
            slot.reserved_by = None
            slot.occupied_by = car.car_id
            car.state = "parked"
            car.x, car.y = slot.x, slot.y
            car.parked_for = self.rng.uniform(28, 90)
            self.last_event = f"Cảm biến xác nhận {slot.slot_id} đã có xe"
        elif car.state == "leaving":
            self.exit_barrier_open = True
            self.last_plate = car.plate
            self.last_event = f"Thanh toán không tiền mặt: {car.plate}"
            car.state = "waiting"
            car.slot_id = None
            car.wait_for = self.rng.uniform(10, 38)
            self.completed_trips += 1

    def traffic_factor(self, car: Car, dx: float, dy: float, distance: float) -> float:
        if distance < 0.001:
            return 1.0
        ux, uy = dx / distance, dy / distance
        factor = 1.0
        for other in self.cars:
            if other is car or other.state not in {"entering", "leaving"}:
                continue
            ox, oy = other.x - car.x, other.y - car.y
            gap = math.hypot(ox, oy)
            if gap < 52 and ox * ux + oy * uy > 0:
                factor = min(factor, max(0.06, (gap - 21) / 31))
        return factor

    def move_car(self, car: Car, dt: float) -> None:
        if car.route_index >= len(car.route):
            self.finish_route(car)
            return
        tx, ty = car.route[car.route_index]
        dx, dy = tx - car.x, ty - car.y
        distance = math.hypot(dx, dy)
        if distance < 0.001:
            car.route_index += 1
            return
        car.angle = math.degrees(math.atan2(-dy, dx))
        step = car.speed * dt * self.traffic_factor(car, dx, dy, distance)
        if step >= distance:
            car.x, car.y = tx, ty
            car.distance_travelled += distance
            car.route_index += 1
            if car.route_index >= len(car.route):
                self.finish_route(car)
        else:
            car.x += dx / distance * step
            car.y += dy / distance * step
            car.distance_travelled += step

    def update(self, real_dt: float) -> None:
        for action in self.bridge.pop_actions():
            self.handle_action(action)
        if self.paused:
            self.publish_snapshot()
            return

        dt = min(real_dt, 0.05) * self.speed_multiplier
        self.elapsed += dt
        self.entry_barrier_open = any(
            car.state == "entering" and car.distance_travelled < 65 for car in self.cars
        )
        self.exit_barrier_open = any(
            car.state == "leaving" and car.x > 1490 for car in self.cars
        )

        entering_count = sum(car.state == "entering" for car in self.cars)
        leaving_count = sum(car.state == "leaving" for car in self.cars)
        for car in self.cars:
            if car.state == "parked" and car.car_id != self.customer_car_id:
                car.parked_for -= dt
                if car.parked_for <= 0 and leaving_count < 10:
                    if self.start_leaving(car):
                        leaving_count += 1
            elif car.state in {"entering", "leaving"}:
                self.move_car(car, dt)
            elif car.state == "waiting":
                car.wait_for -= dt

        if self.elapsed >= self.next_spawn and entering_count < 9 and self.entry_is_clear():
            ready = [car for car in self.cars if car.state == "waiting" and car.wait_for <= 0]
            free = self.available_slots()
            if ready and free:
                started = self.start_entering(self.rng.choice(ready), self.rng.choice(free))
                if started:
                    self.next_spawn = self.elapsed + self.rng.uniform(0.9, 1.8)

        self.iot_latency_ms = max(12, min(90, self.iot_latency_ms + self.rng.randint(-2, 2)))
        self.sensor_uptime = 99.7 + 0.3 * math.sin(self.elapsed / 17)
        self.publish_snapshot()

    def publish_snapshot(self) -> None:
        occupied = sum(slot.occupied_by is not None for slot in self.slots)
        reserved = sum(slot.reserved_by is not None for slot in self.slots)
        moving = sum(car.state in {"entering", "leaving"} for car in self.cars)
        customer = next((car for car in self.cars if car.car_id == self.customer_car_id), None)
        customer_slot = customer.slot_id if customer else None
        slots_json = []
        for slot in self.slots:
            if slot.slot_id == customer_slot and slot.occupied_by == self.customer_car_id:
                status = "mine"
            elif slot.occupied_by is not None:
                status = "busy"
            elif slot.reserved_by is not None:
                status = "reserved"
            else:
                status = "free"
            slots_json.append(
                {
                    "id": slot.slot_id,
                    "zone": slot.zone,
                    "status": status,
                    "electric": slot.electric,
                    "accessible": slot.accessible,
                }
            )
        self.bridge.set_snapshot(
            {
                "timestamp": time.time(),
                "capacity": len(self.slots),
                "free": len(self.slots) - occupied - reserved,
                "occupied": occupied,
                "reserved": reserved,
                "moving": moving,
                "fleet": len(self.cars),
                "completed": self.completed_trips,
                "message": self.message,
                "target": self.guide_target,
                "algorithm": "A* với trọng số ùn tắc",
                "route_distance": round(self.guide_distance),
                "route_nodes": len(self.guide_path),
                "expanded_nodes": self.guide_expanded,
                "astar_calls": self.astar_calls,
                "last_plate": self.last_plate,
                "last_event": self.last_event,
                "iot_latency": self.iot_latency_ms,
                "sensor_uptime": round(self.sensor_uptime, 2),
                "entry_barrier": self.entry_barrier_open,
                "exit_barrier": self.exit_barrier_open,
                "customer_plate": customer.plate if customer else "---",
                "slots": slots_json,
            }
        )

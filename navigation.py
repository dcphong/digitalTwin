"""Graph làn đường và thuật toán A* có trọng số ùn tắc."""

from __future__ import annotations

import heapq
import math

from config import (
    ELEVATOR,
    ENTRY,
    ENTRY_AXIS_X,
    EXIT_AXIS_X,
    EXIT_POINT,
    LANE_Y,
    SLOT_X,
)
from models import ParkingSlot

Point = tuple[float, float]


class LaneGraph:
    def __init__(self, slots: list[ParkingSlot]) -> None:
        self.edges: dict[Point, set[Point]] = {}
        self._build(slots)

    def connect(self, first: Point, second: Point) -> None:
        self.edges.setdefault(first, set()).add(second)
        self.edges.setdefault(second, set()).add(first)

    def _build(self, slots: list[ParkingSlot]) -> None:
        xs = [ENTRY_AXIS_X, *SLOT_X, EXIT_AXIS_X]
        road_ys = [*LANE_Y, 925.0]
        for y in road_ys:
            for left, right in zip(xs, xs[1:]):
                self.connect((left, y), (right, y))
        for x in (ENTRY_AXIS_X, EXIT_AXIS_X):
            ys = [55.0, *LANE_Y, 925.0]
            for top, bottom in zip(ys, ys[1:]):
                self.connect((x, top), (x, bottom))
        self.connect(ENTRY, (ENTRY_AXIS_X, 925.0))
        self.connect((EXIT_AXIS_X, 925.0), EXIT_POINT)
        self.connect(ELEVATOR, (ENTRY_AXIS_X, 55.0))
        for slot in slots:
            self.connect((slot.x, slot.lane_y), (slot.x, slot.y))

    @staticmethod
    def distance(first: Point, second: Point) -> float:
        return math.hypot(first[0] - second[0], first[1] - second[1])

    def astar(
        self,
        start: Point,
        goal: Point,
        congestion: dict[Point, float] | None = None,
        blocked_nodes: set[Point] | None = None,
    ) -> tuple[list[Point], float, int]:
        congestion = congestion or {}
        blocked_nodes = blocked_nodes or set()
        frontier: list[tuple[float, int, Point]] = [(0.0, 0, start)]
        came_from: dict[Point, Point | None] = {start: None}
        cost_so_far = {start: 0.0}
        serial = 0
        expanded = 0

        while frontier:
            _, _, current = heapq.heappop(frontier)
            expanded += 1
            if current == goal:
                break
            for neighbor in self.edges.get(current, ()):
                if neighbor in blocked_nodes and neighbor != goal:
                    continue
                length = self.distance(current, neighbor)
                dynamic_weight = 1.0 + congestion.get(neighbor, 0.0)
                new_cost = cost_so_far[current] + length * dynamic_weight
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    serial += 1
                    priority = new_cost + self.distance(neighbor, goal)
                    heapq.heappush(frontier, (priority, serial, neighbor))
                    came_from[neighbor] = current

        if goal not in came_from:
            return [], math.inf, expanded
        path: list[Point] = []
        current: Point | None = goal
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path, cost_so_far[goal], expanded

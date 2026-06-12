"""Các model dữ liệu của bãi đỗ xe."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from config import ENTRY


@dataclass
class ParkingSlot:
    slot_id: str
    zone: str
    x: float
    y: float
    lane_y: float
    electric: bool = False
    accessible: bool = False
    occupied_by: int | None = None
    reserved_by: int | None = None
    sensor_online: bool = True


@dataclass
class Car:
    car_id: int
    plate: str
    color: tuple[int, int, int]
    state: str = "waiting"
    x: float = ENTRY[0]
    y: float = ENTRY[1]
    slot_id: str | None = None
    route: list[tuple[float, float]] = field(default_factory=list)
    route_index: int = 0
    speed: float = 120.0
    parked_for: float = 0.0
    wait_for: float = 0.0
    angle: float = 0.0
    distance_travelled: float = 0.0


class SharedBridge:
    """Kênh thread-safe giữa mô phỏng, HTTP server và giao diện."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: dict[str, Any] = {}
        self._actions: list[str] = []

    def set_snapshot(self, snapshot: dict[str, Any]) -> None:
        with self._lock:
            self._snapshot = snapshot

    def get_snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._snapshot)

    def push_action(self, action: str) -> None:
        with self._lock:
            self._actions.append(action)

    def pop_actions(self) -> list[str]:
        with self._lock:
            actions = self._actions[:]
            self._actions.clear()
            return actions


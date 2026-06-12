#!/usr/bin/env python3
"""Điểm khởi chạy Digital Twin Smart Parking."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def ensure_dependencies() -> None:
    try:
        import pygame  # noqa: F401
        import qrcode  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        print("Đang cài pygame-ce, qrcode và Pillow...")
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "pygame-ce>=2.5,<3",
                "qrcode[pil]>=7.4,<9",
            ]
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Digital Twin Smart Parking cho trung tâm thương mại"
    )
    parser.add_argument(
        "--cars",
        type=int,
        default=80,
        help="Số xe mô phỏng, giới hạn từ 50 đến 100 (mặc định: 80)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Cổng HTTP cho giao diện QR (mặc định: 8765)",
    )
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.smoke_test:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    ensure_dependencies()

    from models import SharedBridge
    from simulation import DigitalTwin
    from ui import Dashboard
    from web_server import start_web_server

    car_count = max(50, min(100, args.cars))
    bridge = SharedBridge()
    server, url = start_web_server(bridge, args.port)
    twin = DigitalTwin(car_count, bridge)

    print(f"Digital Twin đang chạy: 100 vị trí, {car_count} xe.")
    print(f"Giao diện khách hàng qua QR: {url}")
    try:
        Dashboard(twin, url, smoke_test=args.smoke_test).run()
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

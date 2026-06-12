# Digital Twin Smart Parking

Mô phỏng bãi đỗ xe thông minh dành cho ô tô trong trung tâm thương mại, kết hợp
Digital Twin, IoT, điều phối giao thông và thuật toán tìm đường A*.

## Tính năng

- 100 vị trí đỗ xe, chia thành các khu A-E.
- Mô phỏng liên tục từ 50 đến 100 xe.
- Cập nhật trạng thái chỗ đỗ theo thời gian thực.
- Tìm chỗ đỗ tối ưu và tìm xe của khách bằng A*.
- QR Code mở giao diện khách hàng trên điện thoại cùng mạng Wi-Fi.
- Mô phỏng camera ANPR, barrier tự động, cảm biến IoT, thanh toán số.
- 10 vị trí hỗ trợ sạc xe điện.
- Dashboard Pygame với font tiếng Việt.

## Chạy dự án

Yêu cầu Python 3.10 trở lên:

```bash
python main.py
```

File `main.py` tự cài các dependency cần thiết nếu máy chưa có.

Tùy chỉnh số xe và cổng HTTP:

```bash
python main.py --cars 100 --port 8765
```

## Điều khiển

- `1`: dẫn đến chỗ đỗ tốt nhất.
- `2`: dẫn đến xe của khách.
- `G`: hiển thị graph A*.
- `Space`: tạm dừng mô phỏng.
- `+` / `-`: thay đổi tốc độ.
- `R`: tạo lại mô phỏng.

## Cấu trúc

```text
main.py          Entry point
simulation.py    Lõi Digital Twin và điều phối xe
navigation.py    Graph làn đường và thuật toán A*
ui.py            Dashboard Pygame
web_server.py    Giao diện khách hàng qua QR
models.py        Model dữ liệu và bridge thread-safe
config.py        Cấu hình hình học và màu sắc
web/             Dashboard web Next.js, Tailwind, shadcn và Motion
```

## Phiên bản Web

```bash
cd web
npm install
npm run dev
```

Mở `http://localhost:3000` để xem dashboard web responsive.

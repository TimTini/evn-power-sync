# evn-power-sync

Đồng bộ lịch ngừng/giảm cung cấp điện từ:

- EVNHCMC: `bdmd.evnhcmc.vn`
- EVNSPC: `cskh.evnspc.vn`

## Chạy local

Chuẩn bị môi trường:

```powershell
uv sync
```

```powershell
uv run evn-power-sync search "ten vi tri"
uv run evn-power-sync init
uv run evn-power-sync schedule --from-date 01-01-2026 --to-date 14-01-2026
```

## GitHub Pages + Actions (không cần server cá nhân)

Luồng:

1. **GitHub Actions** chạy **mỗi ngày** (00:00 giờ VN) → tải danh mục vị trí, index khu vực EVNSPC, lịch ngừng điện → ghi `docs/data/*.json` → commit.
2. **GitHub Pages** host web tĩnh trong `docs/` → đọc file JSON đó.

Thiết lập nhanh:

```powershell
Copy-Item config\locations.json.example config\locations.json
# chỉnh vị trí theo dõi
uv run evn-power-sync export --config config\locations.json --output docs\data\schedule.json
```

Sau khi push lên GitHub:

- Bật **Pages**: branch `master`, folder `/docs`
- Workflow `.github/workflows/sync-evn-data.yml` tự chạy (cron hàng ngày + chạy tay)

Chi tiết: [scripts/setup-github-pages.ps1](scripts/setup-github-pages.ps1)

Web app: `docs/index.html` — fetch `data/schedule.json`, lọc khu vực, hiển thị thời gian/lý do.

Config vị trí (local / tùy chỉnh, không commit mặc định):

```text
config/locations.json   # copy từ config/locations.json.example
```

## GUI

```powershell
uv run evn-power-sync-gui
```

Trong GUI:

1. Bấm **Tải lại vị trí online** để lấy/cache vị trí từ 2 nguồn.
   - Cache được merge theo `source + code`: vị trí cũ vẫn giữ, vị trí trùng được cập nhật bằng dữ liệu mới nhất.
   - Đồng thời quét lịch EVNSPC theo khoảng ngày đang nhập để tạo `area_index.json`.
   - Nhờ index này có thể search khu vực chỉ xuất hiện trong kết quả lịch (tên khu vực chi tiết từ EVNSPC).
2. Search vị trí trong ô search.
3. Chọn vị trí.
4. Bấm **Lưu vị trí theo dõi** nếu muốn lưu vào `locations.json`.
5. Nhập ngày và khu vực EVNSPC nếu cần.
6. Bấm **Lấy lịch**.

Lọc khu vực EVNSPC:

```powershell
uv run evn-power-sync schedule --query "vi tri da luu" --area "khu vuc chi tiet" --from-date 01-01-2026 --to-date 07-01-2026
```

Có thể nhập riêng một trong hai:

```powershell
# Chỉ nhập khu vực chi tiết; script tự dùng các vị trí EVNSPC đã init để tìm lịch.
uv run evn-power-sync schedule --area "khu vuc chi tiet" --from-date 01-01-2026 --to-date 07-01-2026

# Chỉ nhập vị trí đã init; script in toàn bộ lịch của vị trí đó.
uv run evn-power-sync schedule --query "vi tri da luu" --from-date 01-01-2026 --to-date 07-01-2026
```

Config vị trí lưu tại (local):

```text
[user-home]/.evn-power-sync/locations.json
```

Index khu vực EVNSPC lưu tại (local):

```text
[user-home]/.evn-power-sync/area_index.json
```

# evn-power-sync

Đồng bộ lịch ngừng/giảm cung cấp điện từ:

- EVNHCMC: `bdmd.evnhcmc.vn`
- EVNSPC: `cskh.evnspc.vn`

## Chạy

Chuẩn bị môi trường:

```powershell
uv sync
```

```powershell
uv run evn-power-sync search "hanh thong"
uv run evn-power-sync search "lap vo"
uv run evn-power-sync init
uv run evn-power-sync schedule --from-date 22-06-2026 --to-date 02-07-2026
```

## GUI

```powershell
uv run evn-power-sync-gui
```

Trong GUI:

1. Bấm **Tải lại vị trí online** để lấy/cache vị trí từ 2 nguồn.
2. Search vị trí trong ô search.
3. Chọn vị trí.
4. Bấm **Lưu vị trí theo dõi** nếu muốn lưu vào `locations.json`.
5. Nhập ngày và khu vực EVNSPC nếu cần.
6. Bấm **Lấy lịch**.

Lọc khu vực EVNSPC:

```powershell
uv run evn-power-sync schedule --query "lap vo" --area "Cống Bảy Di" --from-date 22-06-2026 --to-date 26-06-2026
```

Có thể nhập riêng một trong hai:

```powershell
# Chỉ nhập khu vực chi tiết; script tự dùng các vị trí EVNSPC đã init để tìm lịch.
uv run evn-power-sync schedule --area "Cống Bảy Di" --from-date 22-06-2026 --to-date 26-06-2026

# Chỉ nhập vị trí đã init; script in toàn bộ lịch của vị trí đó.
uv run evn-power-sync schedule --query "lap vo" --from-date 22-06-2026 --to-date 26-06-2026
```

Config vị trí lưu tại:

```text
%USERPROFILE%\.evn-power-sync\locations.json
```

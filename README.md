# evn-power-sync

Đồng bộ lịch ngừng/giảm cung cấp điện từ:

- EVNHCMC: `bdmd.evnhcmc.vn`
- EVNSPC: `cskh.evnspc.vn`

## Chạy

```powershell
python -m evn_power_sync.cli search "hanh thong"
python -m evn_power_sync.cli search "lap vo"
python -m evn_power_sync.cli init
python -m evn_power_sync.cli schedule --from-date 22-06-2026 --to-date 02-07-2026
```

Lọc khu vực EVNSPC:

```powershell
python -m evn_power_sync.cli schedule --query "lap vo" --area "Cống Bảy Di" --from-date 22-06-2026 --to-date 26-06-2026
```

Config vị trí lưu tại:

```text
%USERPROFILE%\.evn-power-sync\locations.json
```

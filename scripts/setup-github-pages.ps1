# GitHub Pages + Actions (không cần server cá nhân)

Hướng dẫn bật web app tĩnh và job sync hàng ngày trên GitHub.

## 1. Chuẩn bị config vị trí theo dõi

```powershell
Copy-Item config\locations.json.example config\locations.json
# Sửa config\locations.json theo khu vực bạn theo dõi (file này mặc định không commit)
```

## 2. Push repo lên GitHub

```powershell
git remote add origin https://github.com/<user>/evn-power-sync.git
git push -u origin master
```

## 3. Bật GitHub Pages

Trên GitHub: **Settings → Pages**

- **Source:** Deploy from a branch
- **Branch:** `master`
- **Folder:** `/docs`

Sau vài phút, web app tại:

```text
https://<user>.github.io/evn-power-sync/
```

## 4. Job sync mỗi ngày

Workflow: `.github/workflows/sync-evn-data.yml`

- Cron: `0 17 * * *` UTC (~00:00 giờ Việt Nam)
- `workflow_dispatch`: chạy tay trên tab Actions
- Các bước:
  1. `export-locations` → `docs/data/locations.json`
  2. `export-area-index` → `docs/data/area_index.json`
  3. `export` (lịch theo `config/locations.json`) → `docs/data/schedule.json`
- Commit + push nếu dữ liệu đổi

## 5. Kiểm tra local

```powershell
uv sync
uv run evn-power-sync export-locations --output docs\data\locations.json
uv run evn-power-sync export-area-index --output docs\data\area_index.json
uv run evn-power-sync export --config config\locations.json --output docs\data\schedule.json
```

## PASS / FAIL

| Bước | PASS khi |
|------|----------|
| Export local | `docs/data/*.json` có `generated_at` |
| Workflow | Actions job xanh, commit `chore: sync EVN locations and outage data` (nếu có thay đổi) |
| Pages | URL GitHub Pages load được |

## Ghi chú

- `config/locations.json` gitignore — không đưa địa chỉ cá nhân lên GitHub trừ khi bạn chủ đích `git add -f`.
- Lịch GitHub Actions có thể trễ vài phút đến vài chục phút khi tải cao.
- `export-area-index` quét lịch EVNSPC theo khoảng ngày — có thể mất vài phút trên Actions.

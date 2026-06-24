# GitHub Pages + Actions (không cần server cá nhân)

Hướng dẫn bật web app tĩnh và job sync lịch trên GitHub.

## 1. Chuẩn bị config vị trí

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

Web đọc cố định `docs/data/schedule.json` (cùng origin, không cần API server).

## 4. Job sync mỗi ngày

Workflow: `.github/workflows/sync-schedule.yml`

- Cron: `0 17 * * *` UTC (~00:00 giờ Việt Nam, mỗi ngày một lần)
- `workflow_dispatch`: chạy tay trên tab Actions
- Lệnh: `uv run evn-power-sync export --config config/locations.json --output docs/data/schedule.json`
- Commit + push nếu dữ liệu đổi
- Nếu chưa có `config/locations.json`, workflow dùng bản `.example`

## 5. Kiểm tra local

```powershell
uv sync
uv run evn-power-sync export --config config\locations.json --output docs\data\schedule.json
# Mở docs\index.html trong browser (hoặc dùng static server nhỏ)
```

## PASS / FAIL

| Bước | PASS khi |
|------|----------|
| Export local | `docs/data/schedule.json` có `generated_at` và `events` |
| Workflow | Actions job xanh, commit `chore: sync outage schedule` (nếu có thay đổi) |
| Pages | URL GitHub Pages load được, hiện meta + danh sách sự kiện |

## Ghi chú

- Repo private: vẫn chạy Actions; Pages public có thể cần GitHub Pro tùy visibility.
- Lịch GitHub Actions có thể trễ vài phút đến vài chục phút khi tải cao.
- Nếu EVN chặn IP datacenter, job có thể fail — xem log Actions.

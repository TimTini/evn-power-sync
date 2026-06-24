from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Any

from .area_index import export_area_index, search_area_index
from .hcmc import VN_TZ, fetch_hcmc_plans, normalize_hcmc_plans, search_hcmc_locations
from .locations_store import export_locations_cache, load_locations_export_rows
from .models import OutageEvent, build_schedule_payload, render_schedule, search_locations
from .spc import fetch_spc_schedule, normalize_spc_schedule, search_spc_locations

APP_DIR = Path.home() / ".evn-power-sync"
DEFAULT_CONFIG_PATH = APP_DIR / "locations.json"
REPO_CONFIG_PATH = Path("config/locations.json")


def resolve_config_path(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    env_path = os.environ.get("EVN_POWER_SYNC_CONFIG")
    if env_path:
        return Path(env_path)
    if REPO_CONFIG_PATH.exists():
        return REPO_CONFIG_PATH
    return DEFAULT_CONFIG_PATH


def _load_locations(config_path: Path | None = None) -> list[dict[str, Any]]:
    path = config_path or resolve_config_path()
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_locations(locations: list[dict[str, Any]], config_path: Path | None = None) -> None:
    path = config_path or resolve_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(locations, ensure_ascii=False, indent=2), encoding="utf-8")


def default_date_range(days_ahead: int = 14) -> tuple[str, str]:
    today = datetime.now(VN_TZ).date()
    return today.strftime("%d-%m-%Y"), (today + timedelta(days=days_ahead)).strftime("%d-%m-%Y")


def _choose_location(query: str) -> dict[str, Any]:
    candidates = search_hcmc_locations(query) + search_spc_locations(query)
    if not candidates:
        raise SystemExit("Không tìm thấy vị trí.")

    for index, item in enumerate(candidates[:10], start=1):
        province = f" - {item.get('province')}" if item.get("province") else ""
        print(f"{index}. [{item['source']}] {item['name']} ({item['code']}){province}")

    raw_choice = input("Chọn số vị trí: ").strip()
    choice = int(raw_choice or "1")
    if choice < 1 or choice > min(10, len(candidates)):
        raise SystemExit("Số chọn không hợp lệ.")
    return candidates[choice - 1]


def cmd_init(args: argparse.Namespace) -> None:
    config_path = resolve_config_path(args.config)
    locations: list[dict[str, Any]] = []
    print("Nhập vị trí cần theo dõi. Enter trống để dừng.")
    while True:
        query = input("Search vị trí: ").strip()
        if not query:
            break
        locations.append(_choose_location(query))
    _save_locations(locations, config_path)
    print(f"Đã lưu {len(locations)} vị trí vào {config_path}")


def cmd_search(args: argparse.Namespace) -> None:
    candidates = search_hcmc_locations(args.query) + search_spc_locations(args.query)
    for index, item in enumerate(candidates[: args.limit], start=1):
        province = f" - {item.get('province')}" if item.get("province") else ""
        print(f"{index}. [{item['source']}] {item['name']} ({item['code']}){province}")


def resolve_schedule_locations(
    initialized_locations: list[dict[str, Any]],
    query: str | None,
    area: str | None,
    area_index_matches: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if query:
        matched = search_locations(initialized_locations, query)
        if matched:
            return matched
        return search_hcmc_locations(query) + search_spc_locations(query)

    if area:
        spc_locations = [location for location in initialized_locations if location.get("source") == "evnspc"]
        if spc_locations:
            return spc_locations
        if area_index_matches is None:
            area_index_matches = search_area_index(area)
        return area_index_matches or initialized_locations

    return initialized_locations


def _events_for_location(location: dict[str, Any], args: argparse.Namespace):
    if location["source"] == "evnhcmc":
        payload = fetch_hcmc_plans(args.from_date.replace("-", "/"), args.to_date.replace("-", "/"), location["code"])
        events = normalize_hcmc_plans(payload, location_query=location["name"])
        for event in events:
            event.ward = location["name"]
        return events

    html = fetch_spc_schedule(location["code"], args.from_date, args.to_date)
    query = args.area or location.get("area") or ""
    return normalize_spc_schedule(
        html,
        location_query=query,
        province=location.get("province"),
        power_company=location.get("name") or location.get("power_company"),
    )


def collect_schedule_events(
    locations: list[dict[str, Any]],
    args: argparse.Namespace,
) -> list[OutageEvent]:
    events: list[OutageEvent] = []
    for location in locations:
        events.extend(_events_for_location(location, args))
    return events


def cmd_schedule(args: argparse.Namespace) -> None:
    config_path = resolve_config_path(args.config)
    locations = resolve_schedule_locations(_load_locations(config_path), args.query, args.area)
    if not locations:
        raise SystemExit(f"Chưa có vị trí trong {config_path}. Chạy: evn-power-sync init")

    from_date, to_date = default_date_range()
    if not getattr(args, "from_date", None):
        args.from_date = from_date
    if not getattr(args, "to_date", None):
        args.to_date = to_date

    events = collect_schedule_events(locations, args)
    print(render_schedule(events))


def cmd_export(args: argparse.Namespace) -> None:
    config_path = resolve_config_path(args.config)
    locations = resolve_schedule_locations(_load_locations(config_path), args.query, args.area)
    if not locations:
        raise SystemExit(f"Chưa có vị trí trong {config_path}. Tạo file config trước khi export.")

    from_date, to_date = default_date_range(args.days_ahead)
    from_date = args.from_date or from_date
    to_date = args.to_date or to_date
    schedule_args = argparse.Namespace(
        from_date=from_date,
        to_date=to_date,
        area=args.area,
    )
    events = collect_schedule_events(locations, schedule_args)
    payload = build_schedule_payload(
        events,
        generated_at=datetime.now(VN_TZ),
        from_date=from_date,
        to_date=to_date,
        locations=locations,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã ghi {len(events)} sự kiện vào {output_path}")


def cmd_export_locations(args: argparse.Namespace) -> None:
    output_path = Path(args.output)
    locations = export_locations_cache(output_path)
    print(f"Đã ghi {len(locations)} vị trí vào {output_path}")


def cmd_export_area_index(args: argparse.Namespace) -> None:
    locations_path = Path(args.locations)
    output_path = Path(args.output)
    from_date, to_date = default_date_range(args.days_ahead)
    from_date = args.from_date or from_date
    to_date = args.to_date or to_date

    all_locations = load_locations_export_rows(locations_path)
    spc_locations = [location for location in all_locations if location.get("source") == "evnspc" and location.get("code")]
    if not spc_locations:
        raise SystemExit(f"Không có vị trí EVNSPC trong {locations_path}.")

    entries = export_area_index(spc_locations, output_path, from_date, to_date)
    print(f"Đã ghi {len(entries)} khu vực vào {output_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Đồng bộ lịch ngừng/giảm cung cấp điện EVNHCMC + EVNSPC")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_config_arg(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--config", help="Đường dẫn locations.json (mặc định: config/locations.json hoặc ~/.evn-power-sync/locations.json)")

    def add_schedule_date_args(parser: argparse.ArgumentParser, *, required: bool) -> None:
        parser.add_argument("--from-date", required=required, help="EVNSPC: dd-mm-yyyy; EVNHCMC tự đổi thành dd/mm/yyyy")
        parser.add_argument("--to-date", required=required, help="EVNSPC: dd-mm-yyyy; EVNHCMC tự đổi thành dd/mm/yyyy")

    init_parser = subparsers.add_parser("init", help="Khởi tạo vị trí theo dõi một lần")
    add_config_arg(init_parser)
    init_parser.set_defaults(func=cmd_init)

    search_parser = subparsers.add_parser("search", help="Search vị trí từ 2 nguồn")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.set_defaults(func=cmd_search)

    schedule_parser = subparsers.add_parser("schedule", help="In lịch cho vị trí đã lưu")
    add_config_arg(schedule_parser)
    add_schedule_date_args(schedule_parser, required=False)
    schedule_parser.add_argument("--query", help="Lọc vị trí đã lưu")
    schedule_parser.add_argument("--area", help="Lọc khu vực chi tiết trong lịch EVNSPC")
    schedule_parser.set_defaults(func=cmd_schedule)

    export_parser = subparsers.add_parser("export", help="Ghi lịch ra JSON cho GitHub Pages / Actions")
    add_config_arg(export_parser)
    add_schedule_date_args(export_parser, required=False)
    export_parser.add_argument("--days-ahead", type=int, default=14, help="Khi không truyền --to-date: số ngày tính từ hôm nay (VN)")
    export_parser.add_argument("--query", help="Lọc vị trí đã lưu")
    export_parser.add_argument("--area", help="Lọc khu vực chi tiết trong lịch EVNSPC")
    export_parser.add_argument("--output", default="docs/data/schedule.json", help="File JSON đầu ra")
    export_parser.set_defaults(func=cmd_export)

    export_locations_parser = subparsers.add_parser("export-locations", help="Tải và ghi danh mục vị trí EVN ra JSON")
    export_locations_parser.add_argument("--output", default="docs/data/locations.json", help="File JSON đầu ra")
    export_locations_parser.set_defaults(func=cmd_export_locations)

    export_area_index_parser = subparsers.add_parser("export-area-index", help="Quét lịch EVNSPC và ghi index khu vực ra JSON")
    add_schedule_date_args(export_area_index_parser, required=False)
    export_area_index_parser.add_argument("--days-ahead", type=int, default=14, help="Khi không truyền --to-date: số ngày tính từ hôm nay (VN)")
    export_area_index_parser.add_argument("--locations", default="docs/data/locations.json", help="File locations.json đã export")
    export_area_index_parser.add_argument("--output", default="docs/data/area_index.json", help="File JSON đầu ra")
    export_area_index_parser.set_defaults(func=cmd_export_area_index)
    return parser


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

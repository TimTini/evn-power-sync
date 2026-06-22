from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .hcmc import fetch_hcmc_plans, normalize_hcmc_plans, search_hcmc_locations
from .models import render_schedule, search_locations
from .spc import fetch_spc_schedule, normalize_spc_schedule, search_spc_locations

APP_DIR = Path.home() / ".evn-power-sync"
CONFIG_PATH = APP_DIR / "locations.json"


def _load_locations() -> list[dict[str, Any]]:
    if not CONFIG_PATH.exists():
        return []
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _save_locations(locations: list[dict[str, Any]]) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(locations, ensure_ascii=False, indent=2), encoding="utf-8")


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
    locations: list[dict[str, Any]] = []
    print("Nhập vị trí cần theo dõi. Enter trống để dừng.")
    while True:
        query = input("Search vị trí: ").strip()
        if not query:
            break
        locations.append(_choose_location(query))
    _save_locations(locations)
    print(f"Đã lưu {len(locations)} vị trí vào {CONFIG_PATH}")


def cmd_search(args: argparse.Namespace) -> None:
    candidates = search_hcmc_locations(args.query) + search_spc_locations(args.query)
    for index, item in enumerate(candidates[: args.limit], start=1):
        province = f" - {item.get('province')}" if item.get("province") else ""
        print(f"{index}. [{item['source']}] {item['name']} ({item['code']}){province}")


def _events_for_location(location: dict[str, Any], args: argparse.Namespace):
    if location["source"] == "evnhcmc":
        payload = fetch_hcmc_plans(args.from_date.replace("-", "/"), args.to_date.replace("-", "/"), location["code"])
        events = normalize_hcmc_plans(payload, location_query=location["name"])
        for event in events:
            event.ward = location["name"]
        return events

    html = fetch_spc_schedule(location["code"], args.from_date, args.to_date)
    query = args.area or ""
    return normalize_spc_schedule(
        html,
        location_query=query,
        province=location.get("province"),
        power_company=location.get("name"),
    )


def cmd_schedule(args: argparse.Namespace) -> None:
    locations = _load_locations()
    if args.query:
        locations = search_locations(locations, args.query)
    if not locations:
        raise SystemExit(f"Chưa có vị trí. Chạy: python -m evn_power_sync.cli init")

    events = []
    for location in locations:
        events.extend(_events_for_location(location, args))
    print(render_schedule(events))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Đồng bộ lịch ngừng/giảm cung cấp điện EVNHCMC + EVNSPC")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Khởi tạo vị trí theo dõi một lần")
    init_parser.set_defaults(func=cmd_init)

    search_parser = subparsers.add_parser("search", help="Search vị trí từ 2 nguồn")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.set_defaults(func=cmd_search)

    schedule_parser = subparsers.add_parser("schedule", help="In lịch cho vị trí đã lưu")
    schedule_parser.add_argument("--from-date", default="22-06-2026", help="EVNSPC: dd-mm-yyyy; EVNHCMC tự đổi thành dd/mm/yyyy")
    schedule_parser.add_argument("--to-date", default="02-07-2026", help="EVNSPC: dd-mm-yyyy; EVNHCMC tự đổi thành dd/mm/yyyy")
    schedule_parser.add_argument("--query", help="Lọc vị trí đã lưu")
    schedule_parser.add_argument("--area", help="Lọc khu vực chi tiết trong lịch EVNSPC")
    schedule_parser.set_defaults(func=cmd_schedule)
    return parser


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

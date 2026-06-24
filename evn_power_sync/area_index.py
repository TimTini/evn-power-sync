from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .locations_store import APP_DIR
from .models import search_locations
from .spc import fetch_spc_schedule, normalize_spc_schedule

AREA_INDEX_PATH = APP_DIR / "area_index.json"


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _write_json_list(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def load_area_index(path: Path = AREA_INDEX_PATH) -> list[dict[str, Any]]:
    return _read_json_list(path)


def load_area_index_export_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        rows = data.get("entries", [])
        return rows if isinstance(rows, list) else []
    if isinstance(data, list):
        return data
    return []


def export_area_index(
    spc_locations: list[dict[str, Any]],
    output_path: Path,
    from_date: str,
    to_date: str,
) -> list[dict[str, Any]]:
    import tempfile
    from datetime import datetime

    from .hcmc import VN_TZ
    from .models import build_area_index_payload

    with tempfile.TemporaryDirectory() as tmp:
        index_path = Path(tmp) / "area_index.json"
        save_area_index(load_area_index_export_rows(output_path), index_path)
        entries = refresh_area_index(spc_locations, from_date, to_date, index_path)

    payload = build_area_index_payload(
        entries,
        generated_at=datetime.now(VN_TZ),
        from_date=from_date,
        to_date=to_date,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return entries


def save_area_index(entries: list[dict[str, Any]], path: Path = AREA_INDEX_PATH) -> None:
    _write_json_list(path, entries)


def _entry_key(entry: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    return entry.get("source"), entry.get("code"), entry.get("area")


def merge_area_entries(
    old_entries: list[dict[str, Any]],
    new_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged_by_key = {_entry_key(entry): dict(entry) for entry in old_entries}
    order = [_entry_key(entry) for entry in old_entries]

    for entry in new_entries:
        key = _entry_key(entry)
        if key not in merged_by_key:
            order.append(key)
        merged_by_key[key] = dict(entry)

    return [merged_by_key[key] for key in order]


def build_area_entries(
    location: dict[str, Any],
    schedule_html: str,
    from_date: str,
    to_date: str,
) -> list[dict[str, Any]]:
    events = normalize_spc_schedule(
        schedule_html,
        location_query="",
        province=location.get("province"),
        power_company=location.get("name"),
    )
    entries: list[dict[str, Any]] = []
    for event in events:
        entries.append(
            {
                "source": "evnspc",
                "code": location.get("code"),
                "province": location.get("province"),
                "power_company": location.get("name"),
                "area": event.area,
                "reason": event.reason,
                "from_date": from_date,
                "to_date": to_date,
                "start_at": event.start_at.isoformat(),
                "end_at": event.end_at.isoformat(),
            }
        )
    return entries


def refresh_area_index(
    locations: list[dict[str, Any]],
    from_date: str,
    to_date: str,
    path: Path = AREA_INDEX_PATH,
) -> list[dict[str, Any]]:
    latest_entries: list[dict[str, Any]] = []
    for location in locations:
        if location.get("source") != "evnspc" or not location.get("code"):
            continue
        html = fetch_spc_schedule(location["code"], from_date, to_date)
        latest_entries.extend(build_area_entries(location, html, from_date, to_date))

    combined = merge_area_entries(load_area_index(path), latest_entries)
    save_area_index(combined, path)
    return combined


def search_area_index(
    query: str,
    path: Path = AREA_INDEX_PATH,
    limit: int = 50,
) -> list[dict[str, Any]]:
    return search_locations(load_area_index(path), query, limit=limit)

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .hcmc import fetch_administratives
from .models import search_locations
from .spc import fetch_power_companies, PROVINCES

APP_DIR = Path.home() / ".evn-power-sync"
TRACKED_LOCATIONS_PATH = APP_DIR / "locations.json"
CACHED_LOCATIONS_PATH = APP_DIR / "locations_cache.json"


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return data


def _write_json_list(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cached_locations(path: Path = CACHED_LOCATIONS_PATH) -> list[dict[str, Any]]:
    return _read_json_list(path)


def save_cached_locations(locations: list[dict[str, Any]], path: Path = CACHED_LOCATIONS_PATH) -> None:
    _write_json_list(path, locations)


def load_tracked_locations(path: Path = TRACKED_LOCATIONS_PATH) -> list[dict[str, Any]]:
    return _read_json_list(path)


def save_tracked_locations(locations: list[dict[str, Any]], path: Path = TRACKED_LOCATIONS_PATH) -> None:
    _write_json_list(path, locations)


def add_tracked_location(location: dict[str, Any], path: Path = TRACKED_LOCATIONS_PATH) -> list[dict[str, Any]]:
    locations = load_tracked_locations(path)
    key = (location.get("source"), location.get("code"))
    if not any((item.get("source"), item.get("code")) == key for item in locations):
        locations.append(location)
        save_tracked_locations(locations, path)
    return locations


def refresh_locations_cache(path: Path = CACHED_LOCATIONS_PATH) -> list[dict[str, Any]]:
    hcmc_locations = [
        {"source": "evnhcmc", "code": row.get("code"), "name": row.get("name"), "level": row.get("lvl")}
        for row in fetch_administratives()
        if row.get("lvl") == 3
    ]

    spc_locations: list[dict[str, Any]] = []
    for parent_code in PROVINCES:
        spc_locations.extend(fetch_power_companies(parent_code))

    combined = hcmc_locations + spc_locations
    save_cached_locations(combined, path)
    return combined


def search_cached_locations(
    query: str,
    path: Path = CACHED_LOCATIONS_PATH,
    limit: int = 50,
) -> list[dict[str, Any]]:
    return search_locations(load_cached_locations(path), query, limit=limit)

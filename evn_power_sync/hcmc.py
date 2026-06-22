from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any
import json
import urllib.parse
import urllib.request

from .models import OutageEvent, search_locations

VN_TZ = timezone(timedelta(hours=7))
BASE_URL = "https://bdmd.evnhcmc.vn"


def _get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json, */*",
            "User-Agent": "Mozilla/5.0",
            "Referer": f"{BASE_URL}/vi",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8-sig"))


def _parse_hcmc_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).astimezone(VN_TZ)


def fetch_administratives() -> list[dict[str, Any]]:
    payload = _get_json(f"{BASE_URL}/api/public/administratives")
    return payload.get("data", [])


def parse_administratives(payload: dict[str, Any], query: str = "") -> list[dict[str, Any]]:
    rows = payload.get("data", payload)
    locations = [
        {
            "source": "evnhcmc",
            "code": row.get("code"),
            "name": row.get("name"),
            "level": row.get("lvl"),
        }
        for row in rows
        if row.get("lvl") == 3
    ]
    return search_locations(locations, query) if query else locations


def search_hcmc_locations(query: str) -> list[dict[str, Any]]:
    return search_locations(
        [
            {"source": "evnhcmc", "code": row.get("code"), "name": row.get("name"), "level": row.get("lvl")}
            for row in fetch_administratives()
            if row.get("lvl") == 3
        ],
        query,
    )


def fetch_hcmc_plans(from_date: str, to_date: str, ward_id: str | None = None) -> dict[str, Any]:
    params = {"fromDate": from_date, "toDate": to_date}
    if ward_id:
        params["wardId"] = ward_id
    return _get_json(f"{BASE_URL}/api/public/plans?{urllib.parse.urlencode(params)}")


def normalize_hcmc_plans(payload: dict[str, Any], location_query: str) -> list[OutageEvent]:
    plans = payload.get("data", {}).get("plans", [])
    events: list[OutageEvent] = []
    for plan in plans:
        stations = [
            station.get("station", {}).get("statioName")
            for station in plan.get("stations", [])
            if station.get("station", {}).get("statioName")
        ]
        events.append(
            OutageEvent(
                source="evnhcmc",
                location_query=location_query,
                area=plan.get("affectedDescription") or "",
                start_at=_parse_hcmc_datetime(plan["fromDate"]),
                end_at=_parse_hcmc_datetime(plan["toDate"]),
                reason=plan.get("description") or "",
                district_or_company=plan.get("provider", {}).get("providerName"),
                stations=stations,
                raw=plan,
            )
        )
    return events

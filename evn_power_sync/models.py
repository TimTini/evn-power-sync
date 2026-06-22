from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import unicodedata


@dataclass(slots=True)
class OutageEvent:
    source: str
    location_query: str
    area: str
    start_at: datetime
    end_at: datetime
    reason: str
    province: str | None = None
    district_or_company: str | None = None
    ward: str | None = None
    stations: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


def fold_text(value: str) -> str:
    text = unicodedata.normalize("NFD", value or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return " ".join(text.lower().split())


def search_locations(locations: list[dict[str, Any]], query: str, limit: int = 20) -> list[dict[str, Any]]:
    needle = fold_text(query)
    if not needle:
        return locations[:limit]

    scored: list[tuple[int, dict[str, Any]]] = []
    for location in locations:
        haystack = fold_text(" ".join(str(v) for v in location.values() if v is not None))
        if needle in haystack:
            scored.append((haystack.index(needle), location))

    return [item for _, item in sorted(scored, key=lambda row: row[0])[:limit]]


def render_schedule(events: list[OutageEvent]) -> str:
    if not events:
        return "Không có lịch ngừng/giảm cung cấp điện cho vị trí và khoảng ngày đã chọn."

    lines: list[str] = []
    for index, event in enumerate(sorted(events, key=lambda item: item.start_at), start=1):
        lines.append(f"{index}. [{event.source}] {event.area}")
        lines.append(f"   Thời gian: {event.start_at:%d/%m/%Y %H:%M} -> {event.end_at:%d/%m/%Y %H:%M}")
        if event.province or event.district_or_company or event.ward:
            parts = [event.province, event.district_or_company, event.ward]
            lines.append("   Vị trí: " + " - ".join(part for part in parts if part))
        if event.stations:
            lines.append("   Trạm: " + ", ".join(event.stations))
        lines.append(f"   Lý do: {event.reason}")
    return "\n".join(lines)

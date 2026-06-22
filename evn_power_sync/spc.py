from __future__ import annotations

from datetime import datetime, timezone, timedelta
from html import unescape
from typing import Any
import re
import urllib.parse
import urllib.request

from .models import OutageEvent, search_locations

VN_TZ = timezone(timedelta(hours=7))
BASE_URL = "https://www.cskh.evnspc.vn"

PROVINCES = {
    "PB07": "Đồng Tháp",
    "PB08": "Tiền Giang",
}


def _get_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html, */*; q=0.01",
            "Accept-Language": "vi,en;q=0.8",
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE_URL}/TraCuu/LichNgungGiamCungCapDien",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _parse_spc_datetime(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%H:%M:%S ngày %d/%m/%Y").replace(tzinfo=VN_TZ)


def parse_power_companies(html: str, province: str | None = None) -> list[dict[str, Any]]:
    companies = []
    for code, label in re.findall(r"<option[^>]*value=[\"']?([^\"'\s>]+)[\"']?[^>]*>(.*?)</option>", html, re.I | re.S):
        name = _strip_html(label)
        if not code or not name:
            continue
        companies.append(
            {
                "source": "evnspc",
                "code": code,
                "name": name,
                "province": PROVINCES.get(code[:4], province),
            }
        )
    return companies


def fetch_power_companies(parent_code: str = "PB07") -> list[dict[str, Any]]:
    html = _get_text(f"{BASE_URL}/TraCuu/GetDanhMucDienLuc?pMA_DVICTREN={urllib.parse.quote(parent_code)}")
    return parse_power_companies(html, province=PROVINCES.get(parent_code))


def search_spc_locations(query: str) -> list[dict[str, Any]]:
    locations: list[dict[str, Any]] = []
    for parent_code in PROVINCES:
        locations.extend(fetch_power_companies(parent_code))
    return search_locations(locations, query)


def fetch_spc_schedule(madvi: str, from_date: str, to_date: str) -> str:
    params = {
        "madvi": madvi,
        "tuNgay": from_date,
        "denNgay": to_date,
        "ChucNang": "MaDonVi",
    }
    return _get_text(
        f"{BASE_URL}/TraCuu/GetThongTinLichNgungGiamCungCapDien?{urllib.parse.urlencode(params)}"
    )


def normalize_spc_schedule(
    html: str,
    location_query: str,
    province: str | None,
    power_company: str | None,
) -> list[OutageEvent]:
    text = _strip_html(html)
    chunks = re.split(r"KHU VỰC:\s*", text)[1:]
    events: list[OutageEvent] = []
    for chunk in chunks:
        match = re.search(
            r"^(.*?)\s*THỜI GIAN:\s*Từ\s*(.*?)\s*đến\s*(.*?)\s*LÝ DO NGỪNG CUNG CẤP ĐIỆN:\s*(.*?)(?=\s*KHU VỰC:|$)",
            chunk,
            re.I,
        )
        if not match:
            continue
        area, start_text, end_text, reason = [part.strip() for part in match.groups()]
        events.append(
            OutageEvent(
                source="evnspc",
                location_query=location_query,
                area=area,
                start_at=_parse_spc_datetime(start_text),
                end_at=_parse_spc_datetime(end_text),
                reason=reason,
                province=province,
                district_or_company=power_company,
                raw={"area": area, "start": start_text, "end": end_text, "reason": reason},
            )
        )
    if location_query:
        events = [event for event in events if search_locations([{"area": event.area}], location_query)]
    return events

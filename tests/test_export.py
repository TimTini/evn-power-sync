import unittest
from datetime import datetime, timezone, timedelta

from evn_power_sync.models import OutageEvent, build_schedule_payload, event_to_dict
from evn_power_sync.cli import default_date_range, resolve_config_path


class ExportTest(unittest.TestCase):
    def test_event_to_dict_serializes_datetime(self):
        vn_tz = timezone(timedelta(hours=7))
        event = OutageEvent(
            source="evnspc",
            location_query="Gamma",
            area="- Khu vực Gamma",
            start_at=datetime(2026, 6, 26, 13, 30, tzinfo=vn_tz),
            end_at=datetime(2026, 6, 26, 15, 0, tzinfo=vn_tz),
            reason="Sửa chữa",
            province="Tỉnh Demo",
            district_or_company="Điện lực Demo",
            stations=["Trạm A"],
        )

        payload = event_to_dict(event)

        self.assertEqual(payload["start_at"], "2026-06-26T13:30:00+07:00")
        self.assertEqual(payload["stations"], ["Trạm A"])

    def test_build_schedule_payload_sorts_events(self):
        vn_tz = timezone(timedelta(hours=7))
        later = OutageEvent(
            source="evnspc",
            location_query="A",
            area="A",
            start_at=datetime(2026, 6, 27, 8, 0, tzinfo=vn_tz),
            end_at=datetime(2026, 6, 27, 9, 0, tzinfo=vn_tz),
            reason="Later",
        )
        earlier = OutageEvent(
            source="evnspc",
            location_query="B",
            area="B",
            start_at=datetime(2026, 6, 26, 8, 0, tzinfo=vn_tz),
            end_at=datetime(2026, 6, 26, 9, 0, tzinfo=vn_tz),
            reason="Earlier",
        )

        payload = build_schedule_payload(
            [later, earlier],
            generated_at=datetime(2026, 6, 24, 10, 0, tzinfo=vn_tz),
            from_date="24-06-2026",
            to_date="08-07-2026",
            locations=[{"source": "evnspc", "code": "XX0001"}],
        )

        self.assertEqual(payload["events"][0]["area"], "B")
        self.assertEqual(payload["from_date"], "24-06-2026")
        self.assertEqual(len(payload["locations"]), 1)

    def test_default_date_range_returns_strings(self):
        from_date, to_date = default_date_range(7)
        self.assertRegex(from_date, r"^\d{2}-\d{2}-\d{4}$")
        self.assertRegex(to_date, r"^\d{2}-\d{2}-\d{4}$")

    def test_resolve_config_path_prefers_explicit(self):
        self.assertEqual(resolve_config_path("custom/locations.json").as_posix(), "custom/locations.json")


if __name__ == "__main__":
    unittest.main()

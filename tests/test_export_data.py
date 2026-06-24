import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evn_power_sync.locations_store import export_locations_cache, load_locations_export_rows
from evn_power_sync.models import build_area_index_payload, build_locations_payload
from evn_power_sync.area_index import export_area_index, load_area_index_export_rows


class ExportDataTest(unittest.TestCase):
    def test_load_locations_export_rows_supports_wrapped_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "locations.json"
            path.write_text(
                json.dumps({"generated_at": "2026-01-01T00:00:00+07:00", "count": 1, "locations": [{"source": "evnspc", "code": "XX0001"}]}),
                encoding="utf-8",
            )
            self.assertEqual(load_locations_export_rows(path)[0]["code"], "XX0001")

    def test_build_locations_payload(self):
        from datetime import datetime, timezone, timedelta

        vn_tz = timezone(timedelta(hours=7))
        payload = build_locations_payload(
            [{"source": "evnspc", "code": "XX0001"}],
            generated_at=datetime(2026, 1, 1, tzinfo=vn_tz),
        )
        self.assertEqual(payload["count"], 1)

    def test_build_area_index_payload(self):
        from datetime import datetime, timezone, timedelta

        vn_tz = timezone(timedelta(hours=7))
        payload = build_area_index_payload(
            [{"area": "Gamma"}],
            generated_at=datetime(2026, 1, 1, tzinfo=vn_tz),
            from_date="01-01-2026",
            to_date="14-01-2026",
        )
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["entries"][0]["area"], "Gamma")

    @patch("evn_power_sync.locations_store.refresh_locations_cache")
    def test_export_locations_cache_writes_wrapped_json(self, refresh_mock):
        refresh_mock.return_value = [{"source": "evnhcmc", "code": "9000001", "name": "Phường Demo"}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "locations.json"
            export_locations_cache(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["count"], 1)
            self.assertIsNotNone(payload["generated_at"])

    @patch("evn_power_sync.area_index.refresh_area_index")
    def test_export_area_index_writes_wrapped_json(self, refresh_mock):
        refresh_mock.return_value = [{"source": "evnspc", "code": "XX0001", "area": "Gamma"}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "area_index.json"
            export_area_index(
                [{"source": "evnspc", "code": "XX0001", "name": "Điện lực Demo"}],
                path,
                "01-01-2026",
                "14-01-2026",
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["count"], 1)
            self.assertEqual(load_area_index_export_rows(path)[0]["area"], "Gamma")


if __name__ == "__main__":
    unittest.main()

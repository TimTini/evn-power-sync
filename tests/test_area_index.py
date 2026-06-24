import tempfile
import unittest
from pathlib import Path

from evn_power_sync.area_index import (
    build_area_entries,
    load_area_index,
    merge_area_entries,
    save_area_index,
    search_area_index,
)


class AreaIndexTest(unittest.TestCase):
    def test_build_area_entries_from_spc_schedule(self):
        html = """KHU VỰC: - Khu vực Gamma xã Delta.
        THỜI GIAN: Từ 13:30:00 ngày 26/06/2026 đến 15:00:00 ngày 26/06/2026
        LÝ DO NGỪNG CUNG CẤP ĐIỆN: Test"""
        location = {
            "source": "evnspc",
            "code": "XX0001",
            "name": "Điện lực Demo",
            "province": "Tỉnh Demo",
        }

        entries = build_area_entries(location, html, "22-06-2026", "26-06-2026")

        self.assertEqual(entries[0]["code"], "XX0001")
        self.assertIn("Gamma", entries[0]["area"])
        self.assertEqual(entries[0]["power_company"], "Điện lực Demo")

    def test_merge_area_entries_keeps_old_and_updates_duplicate_area(self):
        old_entries = [
            {"source": "evnspc", "code": "A", "area": "A old"},
            {"source": "evnspc", "code": "C", "area": "C area", "reason": "old"},
        ]
        new_entries = [
            {"source": "evnspc", "code": "C", "area": "C area", "reason": "new"},
            {"source": "evnspc", "code": "D", "area": "D new"},
        ]

        merged = merge_area_entries(old_entries, new_entries)

        self.assertEqual([(item["code"], item["area"]) for item in merged], [("A", "A old"), ("C", "C area"), ("D", "D new")])
        self.assertEqual(merged[1]["reason"], "new")

    def test_save_and_search_area_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "area_index.json"
            save_area_index(
                [
                    {"source": "evnspc", "code": "XX0001", "area": "- Khu vực Gamma xã Delta."},
                    {"source": "evnspc", "code": "XX0002", "area": "- Khu vực khác."},
                ],
                path,
            )

            found = search_area_index("gamma", path)

            self.assertEqual(load_area_index(path)[0]["code"], "XX0001")
            self.assertEqual(found[0]["code"], "XX0001")


if __name__ == "__main__":
    unittest.main()

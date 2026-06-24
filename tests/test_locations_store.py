import tempfile
import unittest
from pathlib import Path

from evn_power_sync.locations_store import (
    load_cached_locations,
    save_cached_locations,
    search_cached_locations,
    add_tracked_location,
    load_tracked_locations,
    merge_locations_by_identity,
)


class LocationsStoreTest(unittest.TestCase):
    def test_cache_roundtrip_and_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "locations_cache.json"
            locations = [
                {"source": "evnhcmc", "code": "9000001", "name": "Phường Dêmô"},
                {"source": "evnspc", "code": "XX0001", "name": "Điện lực Demo"},
            ]

            save_cached_locations(locations, cache_path)
            found = search_cached_locations("phuong demo", cache_path)

            self.assertEqual(load_cached_locations(cache_path), locations)
            self.assertEqual(found[0]["code"], "9000001")

    def test_add_tracked_location_deduplicates_by_source_and_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracked_path = Path(tmp) / "locations.json"
            location = {"source": "evnspc", "code": "XX0001", "name": "Điện lực Demo"}

            add_tracked_location(location, tracked_path)
            add_tracked_location(location, tracked_path)

            self.assertEqual(load_tracked_locations(tracked_path), [location])

    def test_merge_locations_keeps_old_and_updates_newer_duplicates(self):
        old_locations = [
            {"source": "evnspc", "code": "A", "name": "A old"},
            {"source": "evnspc", "code": "B", "name": "B old"},
            {"source": "evnspc", "code": "C", "name": "C old", "province": "Old"},
        ]
        new_locations = [
            {"source": "evnspc", "code": "C", "name": "C new", "province": "New"},
            {"source": "evnspc", "code": "D", "name": "D new"},
        ]

        merged = merge_locations_by_identity(old_locations, new_locations)

        self.assertEqual([item["code"] for item in merged], ["A", "B", "C", "D"])
        self.assertEqual(merged[2]["name"], "C new")
        self.assertEqual(merged[2]["province"], "New")


if __name__ == "__main__":
    unittest.main()

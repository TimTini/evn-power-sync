import tempfile
import unittest
from pathlib import Path

from evn_power_sync.locations_store import (
    load_cached_locations,
    save_cached_locations,
    search_cached_locations,
    add_tracked_location,
    load_tracked_locations,
)


class LocationsStoreTest(unittest.TestCase):
    def test_cache_roundtrip_and_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "locations_cache.json"
            locations = [
                {"source": "evnhcmc", "code": "7926890", "name": "Phường Hạnh Thông"},
                {"source": "evnspc", "code": "PB0709", "name": "Điện lực Lấp Vò"},
            ]

            save_cached_locations(locations, cache_path)
            found = search_cached_locations("hanh thong", cache_path)

            self.assertEqual(load_cached_locations(cache_path), locations)
            self.assertEqual(found[0]["code"], "7926890")

    def test_add_tracked_location_deduplicates_by_source_and_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracked_path = Path(tmp) / "locations.json"
            location = {"source": "evnspc", "code": "PB0709", "name": "Điện lực Lấp Vò"}

            add_tracked_location(location, tracked_path)
            add_tracked_location(location, tracked_path)

            self.assertEqual(load_tracked_locations(tracked_path), [location])


if __name__ == "__main__":
    unittest.main()

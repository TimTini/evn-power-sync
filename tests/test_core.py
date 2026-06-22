import unittest

from evn_power_sync.hcmc import parse_administratives, normalize_hcmc_plans
from evn_power_sync.spc import parse_power_companies, normalize_spc_schedule
from evn_power_sync.models import search_locations, render_schedule
from evn_power_sync.cli import resolve_schedule_locations


class CoreTest(unittest.TestCase):
    def test_search_locations_matches_accent_insensitive(self):
        locations = [
            {"source": "evnhcmc", "name": "Phường Hạnh Thông", "code": "7926890"},
            {"source": "evnspc", "name": "Điện lực Lấp Vò", "code": "PB0709", "province": "Đồng Tháp"},
        ]

        found = search_locations(locations, "hanh thong")

        self.assertEqual(found[0]["code"], "7926890")

    def test_parse_hcmc_administratives_and_plans(self):
        admin_payload = {"data": [{"code": "7926890", "name": "Phường Hạnh Thông", "lvl": 3}]}
        self.assertEqual(parse_administratives(admin_payload, "Hanh Thong")[0]["code"], "7926890")

        plans_payload = {"data": {"plans": [{
            "planId": "1",
            "fromDate": "2026-06-22T02:00:00.000Z",
            "toDate": "2026-06-22T04:00:00.000Z",
            "affectedDescription": "Một phần Phường Hạnh Thông",
            "description": "Sửa chữa",
            "provider": {"providerName": "Gia Định"},
            "stations": [{"station": {"statioName": "BẾN SỎI 2", "lat": 10.1, "lon": 106.1}}],
        }]}}

        events = normalize_hcmc_plans(plans_payload, location_query="Phường Hạnh Thông")

        self.assertEqual(events[0].source, "evnhcmc")
        self.assertEqual(events[0].area, "Một phần Phường Hạnh Thông")
        self.assertEqual(events[0].start_at.isoformat(), "2026-06-22T09:00:00+07:00")

    def test_parse_spc_company_and_schedule(self):
        options_html = (
            '<option value="PB0709">Điện lực Lấp Vò</option>'
            '<option value="PB0809">Điện lực Cái Bè</option>'
        )
        companies = parse_power_companies(options_html, province="Đồng Tháp")
        self.assertEqual(companies[0]["code"], "PB0709")
        self.assertEqual(companies[0]["province"], "Đồng Tháp")
        self.assertEqual(companies[1]["province"], "Tiền Giang")

        html = """<div>KHU VỰC: - Khu vực Cống Bảy Di xã Mỹ An Hưng.
        THỜI GIAN: Từ 13:30:00 ngày 26/06/2026 đến 15:00:00 ngày 26/06/2026
        LÝ DO NGỪNG CUNG CẤP ĐIỆN: Thí nghiệm, sửa chữa bảo dưỡng Trung, hạ áp</div>"""

        events = normalize_spc_schedule(
            html,
            location_query="Cống Bảy Di",
            province="Đồng Tháp",
            power_company="Điện lực Lấp Vò",
        )

        self.assertEqual(events[0].source, "evnspc")
        self.assertIn("Cống Bảy Di", events[0].area)
        self.assertEqual(events[0].start_at.isoformat(), "2026-06-26T13:30:00+07:00")

    def test_render_schedule_empty_and_events(self):
        self.assertIn("Không có lịch", render_schedule([]))
        html = (
            "KHU VỰC: X THỜI GIAN: Từ 08:00:00 ngày 23/06/2026 "
            "đến 09:00:00 ngày 23/06/2026 LÝ DO NGỪNG CUNG CẤP ĐIỆN: Test"
        )
        events = normalize_spc_schedule(
            html,
            location_query="X",
            province="Đồng Tháp",
            power_company="Điện lực Lấp Vò",
        )

        rendered = render_schedule(events)

        self.assertIn("23/06/2026 08:00", rendered)
        self.assertIn("Test", rendered)

    def test_schedule_can_use_only_area_when_locations_are_initialized(self):
        locations = [
            {"source": "evnhcmc", "name": "Phường Hạnh Thông", "code": "7926890"},
            {"source": "evnspc", "name": "Điện lực Lấp Vò", "code": "PB0709", "province": "Đồng Tháp"},
        ]

        resolved = resolve_schedule_locations(locations, query=None, area="Cống Bảy Di")

        self.assertEqual([item["code"] for item in resolved], ["PB0709"])

    def test_schedule_can_use_area_index_when_locations_are_not_initialized(self):
        resolved = resolve_schedule_locations(
            initialized_locations=[],
            query=None,
            area="Cống Bảy Di",
            area_index_matches=[
                {
                    "source": "evnspc",
                    "code": "PB0709",
                    "power_company": "Điện lực Lấp Vò",
                    "area": "- Khu vực Cống Bảy Di xã Mỹ An Hưng.",
                }
            ],
        )

        self.assertEqual(resolved[0]["code"], "PB0709")

    def test_schedule_can_use_only_query_when_location_is_initialized(self):
        locations = [
            {"source": "evnhcmc", "name": "Phường Hạnh Thông", "code": "7926890"},
            {"source": "evnspc", "name": "Điện lực Lấp Vò", "code": "PB0709", "province": "Đồng Tháp"},
        ]

        resolved = resolve_schedule_locations(locations, query="lap vo", area=None)

        self.assertEqual([item["code"] for item in resolved], ["PB0709"])


if __name__ == "__main__":
    unittest.main()

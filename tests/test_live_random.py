import os
import json
import random
import unittest

from evn_power_sync.hcmc import fetch_administratives, fetch_hcmc_plans, normalize_hcmc_plans
from evn_power_sync.spc import fetch_power_companies, fetch_spc_schedule, normalize_spc_schedule


LIVE_TESTS = os.environ.get("EVN_LIVE_TESTS") == "1"


@unittest.skipUnless(LIVE_TESTS, "set EVN_LIVE_TESTS=1 to run live EVN endpoint tests")
class LiveRandomTest(unittest.TestCase):
    def test_random_hcmc_wards_can_fetch_schedules(self):
        rng = random.Random(20260622)
        wards = [row for row in fetch_administratives() if row.get("lvl") == 3]
        self.assertGreater(len(wards), 0)

        sampled_wards = rng.sample(wards, k=min(3, len(wards)))
        checked = []
        for ward in sampled_wards:
            payload = fetch_hcmc_plans("22/06/2026", "02/07/2026", ward["code"])
            events = normalize_hcmc_plans(payload, location_query=ward["name"])
            self.assertIsInstance(events, list)
            checked.append({"code": ward["code"], "name": ward["name"], "events": len(events)})

        print("HCMC random wards:", json.dumps(checked, ensure_ascii=True))

    def test_random_spc_power_companies_can_fetch_schedules(self):
        rng = random.Random(20260622)
        companies = fetch_power_companies("PB07")
        self.assertGreater(len(companies), 0)

        sampled_companies = rng.sample(companies, k=min(3, len(companies)))
        checked = []
        for company in sampled_companies:
            html = fetch_spc_schedule(company["code"], "22-06-2026", "26-06-2026")
            events = normalize_spc_schedule(
                html,
                location_query="",
                province=company.get("province"),
                power_company=company.get("name"),
            )
            self.assertIsInstance(events, list)
            checked.append({"code": company["code"], "name": company["name"], "events": len(events)})

        print("EVNSPC random companies:", json.dumps(checked, ensure_ascii=True))

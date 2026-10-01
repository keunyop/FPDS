import asyncio
import unittest
from api_service.main import healthz
from worker.pipeline.fpds_collection_accuracy import ACCURACY_VERSION
from worker.pipeline.fpds_market_profile import MARKET_PROFILE_VERSION

class HealthPolicyTests(unittest.TestCase):
    def test_reports_serving_policy_without_private_configuration(self):
        self.assertEqual(asyncio.run(healthz()), {
            "status": "ok", "collection_accuracy_version": ACCURACY_VERSION,
            "market_profile_version": MARKET_PROFILE_VERSION,
        })

from __future__ import annotations

import inspect
import unittest

from api_service.main import app


class ReviewDetailRouteTests(unittest.TestCase):
    def test_detail_route_has_no_audit_background_task_dependency(self) -> None:
        route = next(route for route in app.routes if route.path == "/api/admin/review-tasks/{review_task_id}")

        self.assertEqual(set(inspect.signature(route.endpoint).parameters), {"request", "review_task_id"})

    def test_obsolete_operational_log_routes_are_not_registered(self) -> None:
        paths = {route.path for route in app.routes}

        self.assertNotIn("/api/admin/audit-log", paths)
        self.assertNotIn("/api/admin/llm-usage", paths)


if __name__ == "__main__":
    unittest.main()

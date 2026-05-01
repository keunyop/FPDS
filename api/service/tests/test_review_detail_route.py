from __future__ import annotations

import unittest

from api_service.config import Settings
from api_service.main import _schedule_evidence_trace_viewed_audit


class _RecordingBackgroundTasks:
    def __init__(self) -> None:
        self.tasks: list[tuple[object, dict[str, object]]] = []

    def add_task(self, func, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.tasks.append((func, kwargs))


class ReviewDetailRouteTests(unittest.TestCase):
    def test_detail_audit_is_scheduled_outside_response_path(self) -> None:
        background_tasks = _RecordingBackgroundTasks()
        settings = Settings.from_env()

        _schedule_evidence_trace_viewed_audit(
            background_tasks,  # type: ignore[arg-type]
            settings=settings,
            actor={"user_id": "usr-001", "role": "admin", "display_name": "Ignored"},
            review_task_id="review-001",
            run_id="run-001",
            candidate_id="cand-001",
            product_id=None,
            request_id="req-001",
            ip_address="127.0.0.1",
            user_agent="unit-test",
            field_count=3,
            evidence_item_count=5,
        )

        self.assertEqual(len(background_tasks.tasks), 1)
        _func, kwargs = background_tasks.tasks[0]
        self.assertEqual(kwargs["review_task_id"], "review-001")
        self.assertEqual(kwargs["run_id"], "run-001")
        self.assertEqual(kwargs["candidate_id"], "cand-001")
        self.assertEqual(kwargs["field_count"], 3)
        self.assertEqual(kwargs["actor"], {"user_id": "usr-001", "role": "admin"})


if __name__ == "__main__":
    unittest.main()

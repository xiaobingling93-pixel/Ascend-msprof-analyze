import unittest

from profiler.advisor.analyzer.schedule.gc.gc_checker import GcChecker
from profiler.test.ut.advisor.advisor_backend.tools.tool import recover_env
from profiler.advisor.common.timeline.event import TimelineEvent


class TestGcChecker(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        recover_env()

    def test_no_synchronize_stream(self):
        checker = GcChecker()

        large_free_events = [
            TimelineEvent(dict(ts=1, dur=10)), TimelineEvent(dict(ts=20, dur=100)), TimelineEvent(dict(ts=200, dur=10))
        ]

        checker.max_acl_event_time_ratio = 0.02
        checker.max_acl_event_num_ratio = 0.02
        acl_events = [TimelineEvent(dict(ts=i, dur=0.1)) for i in range(1, 10)] + \
                     [TimelineEvent(dict(ts=i, dur=0.1)) for i in range(20, 21)] + \
                     [TimelineEvent(dict(ts=i, dur=0.1)) for i in range(200, 210)]
        free_event = checker.get_free_events_include_gc(large_free_events, acl_events)
        self.assertEqual(free_event, TimelineEvent(dict(ts=20, dur=100)))

        checker.max_acl_event_num_ratio = 0.001
        free_event = checker.get_free_events_include_gc(large_free_events, acl_events)
        self.assertEqual(free_event, {})

import unittest
from analysis import parse_events,overview,hourly_counts,daily_counts,source_summary

CSV="""timestamp,source_id,channel,outcome
2026-08-01T08:00:00,SRC-A,call,missed
2026-08-01T22:00:00,SRC-A,call,blocked
2026-08-02T11:00:00,SRC-B,call,answered
"""

class TestSignalScope(unittest.TestCase):
    def setUp(self): self.events=parse_events(CSV)
    def test_count(self): self.assertEqual(len(self.events),3)
    def test_sorted(self): self.assertLess(self.events[0]["timestamp"],self.events[1]["timestamp"])
    def test_overview(self): self.assertEqual(overview(self.events)["unanswered_pct"],66.7)
    def test_sources(self): self.assertEqual(overview(self.events)["sources"],2)
    def test_hours(self): self.assertEqual(hourly_counts(self.events)[22],1)
    def test_daily(self): self.assertEqual(daily_counts(self.events)["2026-08-01"],2)
    def test_summary(self): self.assertEqual(sum(x["events"] for x in source_summary(self.events)),3)
    def test_stability(self): self.assertEqual(source_summary(self.events),source_summary(self.events))
    def test_bad_outcome(self):
        with self.assertRaises(ValueError):
            parse_events("timestamp,source_id,channel,outcome\n2026-01-01T10:00:00,A,call,unknown")
    def test_missing_column(self):
        with self.assertRaises(ValueError): parse_events("timestamp,source_id\n2026-01-01,A")
    def test_timezone_mixture(self):
        with self.assertRaises(ValueError):
            parse_events("timestamp,source_id,channel,outcome\n2026-01-01T10:00:00,A,call,missed\n2026-01-01T10:00:00Z,B,call,missed")
    def test_empty(self):
        with self.assertRaises(ValueError): parse_events("timestamp,source_id,channel,outcome\n")

if __name__=="__main__": unittest.main()

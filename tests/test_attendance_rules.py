import unittest
from datetime import time

from bot.services.rules import attendance_percent, period_weekdays, time_in_lesson


class AttendanceRulesTests(unittest.TestCase):
    def test_odd_and_even_weekdays(self):
        self.assertEqual(period_weekdays("odd"), (0, 2, 4))
        self.assertEqual(period_weekdays("even"), (1, 3, 5))

    def test_lesson_time_includes_boundaries(self):
        self.assertTrue(time_in_lesson(time(9, 0), time(9, 0), time(10, 30)))
        self.assertTrue(time_in_lesson(time(10, 30), time(9, 0), time(10, 30)))
        self.assertFalse(time_in_lesson(time(8, 59), time(9, 0), time(10, 30)))
        self.assertFalse(time_in_lesson(time(10, 31), time(9, 0), time(10, 30)))

    def test_attendance_percent(self):
        self.assertEqual(attendance_percent(8, 2), 80.0)
        self.assertEqual(attendance_percent(0, 0), 0.0)
        self.assertEqual(attendance_percent(2, 1), 66.7)


if __name__ == "__main__":
    unittest.main()

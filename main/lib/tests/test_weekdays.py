import unittest
from hypothesis import given
from main.lib import weekdays
import hypothesis.strategies as st
import os

class TestConvertValues(unittest.TestCase):
    @given(st.sampled_from(list(weekdays.DAYWEEK_MAP.values())))
    def test_convert(self, day_str):
        daycode = weekdays.convert(day_str)
        self.assertEqual(len(daycode), 3)

class TestConvertKeys(unittest.TestCase):
    @given(st.sampled_from(list(weekdays.DAYWEEK_MAP.keys())))
    def test_convert(self, day_str):
        daycode = weekdays.convert(day_str)
        self.assertNotEqual(len(daycode), 3)

class TestNextKeys(unittest.TestCase):
    @given(st.sampled_from(list(weekdays.DAYWEEK_MAP.keys())))
    def test_next(self, day_str):
        self.assertNotEqual(day_str, weekdays.next(day_str))

class TestNextValues(unittest.TestCase):
    @given(st.sampled_from(list(weekdays.DAYWEEK_MAP.values())))
    def test_next(self, day_str):
        self.assertNotEqual(day_str, weekdays.next(day_str))

class TestPrevKeys(unittest.TestCase):
    @given(st.sampled_from(list(weekdays.DAYWEEK_MAP.keys())))
    def test_next(self, day_str):
        self.assertNotEqual(day_str, weekdays.prev(day_str))

class TestPrevValues(unittest.TestCase):
    @given(st.sampled_from(list(weekdays.DAYWEEK_MAP.values())))
    def test_next(self, day_str):
        self.assertNotEqual(day_str, weekdays.prev(day_str))

class TestShortcodeKeys(unittest.TestCase):
    @given(st.sampled_from(list(weekdays.DAYWEEK_MAP.keys())))
    def test_next(self, day_str):
        self.assertEqual(3, len(weekdays.to_shortcode(day_str)))

class TestShortcodeValues(unittest.TestCase):
    @given(st.sampled_from(list(weekdays.DAYWEEK_MAP.values())))
    def test_next(self, day_str):
        self.assertEqual(3, len(weekdays.to_shortcode(day_str)))

class TestLongcodeKeys(unittest.TestCase):
    @given(st.sampled_from(list(weekdays.DAYWEEK_MAP.keys())))
    def test_next(self, day_str):
        self.assertNotEqual(3, len(weekdays.to_longcode(day_str)))

class TestLongcodeValues(unittest.TestCase):
    @given(st.sampled_from(list(weekdays.DAYWEEK_MAP.values())))
    def test_next(self, day_str):
        self.assertNotEqual(3, len(weekdays.to_longcode(day_str)))

class TestDayToIndexValues(unittest.TestCase):
    @given(st.sampled_from(list(weekdays.DAYWEEK_MAP.values())))
    def test_day_to_index(self, day_str):
        self.assertIsInstance(weekdays.day_to_index(day_str), int)

class TestDayToIndexKeys(unittest.TestCase):
    @given(st.sampled_from(list(weekdays.DAYWEEK_MAP.keys())))
    def test_day_to_index(self, day_str):
        self.assertIsInstance(weekdays.day_to_index(day_str), int)

class TestIndexToDay(unittest.TestCase):
    @given(st.integers(min_value=0, max_value=6))
    def test_index_to_day(self, idx):
        self.assertIsInstance(weekdays.index_to_day(idx), str)

if __name__ == '__main__':
    unittest.main()

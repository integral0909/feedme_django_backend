from django.test import TestCase, SimpleTestCase
from data_entry.models import parse_time_str, time_unit, Draft, RecipeDraft, IngredientDraft


class TestParseTimeStr(SimpleTestCase):
    def test_parse_time_str(self):
        self.assertEqual(parse_time_str('20 mins'), 1200)
        self.assertEqual(parse_time_str('1 hr 20 mins'), 4800)
        self.assertEqual(parse_time_str('1 hrs, 20 mins'), 4800)
        self.assertEqual(parse_time_str('1 hrous, 20 mins'), 4800)
        self.assertEqual(parse_time_str('1 hrous, 20 mints'), 4800)
        self.assertEqual(parse_time_str('20 mins and 1 hrs'), 4800)


class TestTimeHash(SimpleTestCase):
    def test_time_unit(self):
        self.assertEqual(time_unit('houras'), 'hours')
        self.assertEqual(time_unit('hr'), 'hours')
        self.assertEqual(time_unit('hars'), 'hours')
        self.assertEqual(time_unit('mints'), 'minutes')
        self.assertEqual(time_unit('mins'), 'minutes')
        self.assertEqual(time_unit('minutes'), 'minutes')
        self.assertEqual(time_unit('minute'), 'minutes')
        self.assertEqual(time_unit('min'), 'minutes')


class TestDraftMeta(SimpleTestCase):
    def test_get_related_fields(self):
        self.assertFalse(Draft().get_related_fields())
        self.assertTrue(RecipeDraft().get_related_fields())
        self.assertFalse(IngredientDraft().get_related_fields())

    def test_generate_checksum(self):
        rcpd = RecipeDraft(name_raw='Test')
        self.assertFalse(rcpd.checksum)
        rcpd.generate_checksum()
        self.assertTrue(rcpd.checksum)

    def test_checksum_has_changed(self):
        rcpd = RecipeDraft(name_raw='Test')
        rcpd.generate_checksum()
        self.assertFalse(rcpd.checksum_has_changed())
        rcpd.name_raw = 'New title'
        self.assertTrue(rcpd.checksum_has_changed())
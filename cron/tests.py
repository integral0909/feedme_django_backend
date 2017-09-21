from django.test import TestCase, Client
from unittest.mock import patch
import logging

logging.disable(logging.CRITICAL)


class TestCronJobs(TestCase):
    def setUp(self):
        self.c = Client()

    def test_randomise_dishes(self):
        with patch.dict('os.environ', {'ROLE': 'WORKER'}):
            res = self.c.get('/cron/randomise/dishes/')
            self.assertEqual(res.status_code, 200)

    def test_randomise_recipes(self):
        with patch.dict('os.environ', {'ROLE': 'WORKER'}):
            res = self.c.get('/cron/randomise/recipes/')
            self.assertEqual(res.status_code, 200)

    def test_validate_dishes(self):
        with patch.dict('os.environ', {'ROLE': 'WORKER'}):
            res = self.c.get('/cron/validate/dishes/')
            self.assertEqual(res.status_code, 200)

    def test_validate_recipes(self):
        with patch.dict('os.environ', {'ROLE': 'WORKER'}):
            res = self.c.get('/cron/validate/recipes/')
            self.assertEqual(res.status_code, 200)

    def test_process_draft_recipes(self):
        with patch.dict('os.environ', {'ROLE': 'WORKER'}):
            res = self.c.get('/cron/process/draft/recipes/')
            self.assertEqual(res.status_code, 200)

    def test_process_draft_fail_nonworker_environment(self):
        with patch.dict('os.environ', {'ROLE': ''}):
            res = self.c.get('/cron/process/draft/recipes/')
            self.assertEqual(res.status_code, 400)

    def test_randomise_dishes_fail_nonworker_environment(self):
        with patch.dict('os.environ', {'ROLE': ''}):
            res = self.c.get('/cron/randomise/dishes/')
            self.assertEqual(res.status_code, 400)

    def test_randomise_recipes_fail_nonworker_environment(self):
        with patch.dict('os.environ', {'ROLE': ''}):
            res = self.c.get('/cron/randomise/recipes/')
            self.assertEqual(res.status_code, 400)

    def test_validate_dishes_fail_nonworker_environment(self):
        with patch.dict('os.environ', {'ROLE': ''}):
            res = self.c.get('/cron/validate/dishes/')
            self.assertEqual(res.status_code, 400)

    def test_validate_recipes_fail_nonworker_environment(self):
        with patch.dict('os.environ', {'ROLE': ''}):
            res = self.c.get('/cron/validate/recipes/')
            self.assertEqual(res.status_code, 400)

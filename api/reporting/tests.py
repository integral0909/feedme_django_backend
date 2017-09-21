from django.test import TestCase, Client
from django.contrib.auth.models import User
import logging

logging.disable(logging.CRITICAL)


class TestReportingApi(TestCase):
    def setUp(self):
        users = [
            User.objects.create(email='test@test.test', username='test',
                                first_name='tob', is_staff=True)
        ]
        self.c = Client()
        self.c.force_login(users[0])

    def test_engagement(self):
        res = self.c.get('/api/reporting/engagement/')
        self.assertEqual(res.status_code, 200)

    def test_users(self):
        res = self.c.get('/api/reporting/users/')
        self.assertEqual(res.status_code, 200)

    def test_recent(self):
        res = self.c.get('/api/reporting/recent/')
        self.assertEqual(res.status_code, 200)

    def test_recent_staff_only(self):
        res = Client().get('/api/reporting/recent/')
        self.assertEqual(res.status_code, 403)

    def test_users_staff_only(self):
        res = Client().get('/api/reporting/users/')
        self.assertEqual(res.status_code, 403)

    def test_engagement_staff_only(self):
        res = Client().get('/api/reporting/engagement/')
        self.assertEqual(res.status_code, 403)

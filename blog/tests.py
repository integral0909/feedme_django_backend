from django.test import TestCase, Client
from blog.models import Post
import logging

logging.disable(logging.CRITICAL)


class TestBlogs(TestCase):
    fixtures = ['blog/fixtures/blogs.json']
    def setUp(self):
        self.c = Client()

    def test_display_post(self):
        for p in Post.objects.all():
            res = self.c.get('/blog/%s/' % p.slug)
            self.assertEqual(res.status_code, 200)

    def test_list_posts(self):
        res = self.c.get('/blog/')
        self.assertEqual(res.status_code, 200)

    def test_list_posts_pagination(self):
        res = self.c.get('/blog/', data={'page': 2})
        self.assertEqual(res.status_code, 200)

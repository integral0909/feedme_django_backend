from django.test import TestCase, Client, tag
from main.models import Restaurant, Recipe
from main.lib import weekdays
from api.tests import LoggedInTestcase


class TestRestaurant(TestCase):
    fixtures = ['main/fixtures/all_fixtures_exclude_likes.json']

    def test_openingtimes(self):
        for rest in Restaurant.objects.all():
            tup_list = rest.get_displayable_opening_times()
            prev_day_tup = (0, )
            prev_tup = (0, )
            day_flags = {'mon': False, 'tue': False, 'wed': False, 'thu': False,
                         'fri': False, 'sat': False, 'sun': False}
            for tup in tup_list:
                if prev_tup[0] != tup[0]:
                    prev_day_tup = prev_tup
                if prev_day_tup[0] != 0:
                    self.assertEqual(prev_day_tup[0], weekdays.prev(tup[0])[1])
                day_flags[weekdays.to_shortcode(tup[0])] = True
                prev_tup = tup
            for flag in list(day_flags.values()):
                self.assertTrue(flag)


class TestRecipe(TestCase):
    fixtures = ['fixtures/recipes_with_duplicates2.json']

    def test_recipe(self):
        self.assertTrue(Recipe.objects.all().count())

    def test_time_displays(self):
        for recipe in Recipe.objects.all():
            self.assertTrue(recipe.get_prep_time_display())
            self.assertTrue(recipe.get_cook_time_display())

    def test_source_url_display(self):
        for recipe in Recipe.objects.all():
            if recipe.get_source_url_display() == '':
                continue
            self.assertTrue(recipe.get_source_url_display())

    def test_source_url_display_empty(self):
        rcp = Recipe.objects.all()[0]
        rcp.source_url = ''
        self.assertEqual(rcp.get_source_url_display(), '')
        rcp.source_url = None
        self.assertEqual(rcp.get_source_url_display(), '')


@tag('neo-link')
class TestRecipeNeoLink(TestCase, LoggedInTestcase):
    fixtures = ['fixtures/keywords.json',
                'fixtures/recipes_from_dev.json']

    def setUp(self):
        self.setUp_session()

    def swipe_recipe(self, recipe):
        did_like = bool(recipe['pg_id'] % 2)
        print('swipe:', recipe['name'], '\n\tid:', recipe['pg_id'], '\tdid_like:', did_like)
        self.c.post('/api/likes/recipes/', {'did_like': did_like, 'recipe_id': recipe['pg_id']})

    @tag('slow', 'behaviour')
    def test_example_behaviour(self):
        from time import sleep
        data = self.c.get('/api/recipes/').json()
        print('get page 1')
        data2 = self.c.get(data['next']).json()
        print('get page 2')
        print('iter page 1')
        for recipe in data['results']:
            sleep(0.5)
            self.swipe_recipe(recipe)
        print('get page 3')
        data3 = self.c.get(data2['next']).json()
        print('iter page 2')
        for recipe in data2['results']:
            sleep(0.5)
            self.swipe_recipe(recipe)
        print('get page 4')
        data4 = self.c.get(data3['next']).json()
        print('Complete')


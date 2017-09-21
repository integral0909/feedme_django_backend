import json
from django.test import TestCase, Client
from django.core import management
from django.contrib.auth.models import User
from datetime import timedelta
from main.models import *
from shopping_list.models import ShoppingList, Item, CustomItem
from django.utils import timezone
from api.authentication import FirebaseJWTBackend

logging.disable(logging.CRITICAL)


def create_fixture(app_name, filename):
    print('Creating fixture..')
    with open(filename, 'w') as f:
        management.call_command('dumpdata', app_name, stdout=f)


def turn_off_auto_now(ModelClass, field_name):
    """ref: http://stackoverflow.com/questions/7499767/temporarily-disable-auto-now-auto-now-add"""
    def auto_now_off(field):
        field.auto_now = False
    do_to_model(ModelClass, field_name, auto_now_off)


def turn_off_auto_now_add(ModelClass, field_name):
    def auto_now_add_off(field):
        field.auto_now_add = False
    do_to_model(ModelClass, field_name, auto_now_add_off)


def do_to_model(ModelClass, field_name, func):
    field = ModelClass._meta.get_field(field_name)
    func(field)


def setupDishesAndRestaurants():
    res = Restaurant.objects.create(name='testRes', slug='testres',
                                    image_url='https://example.com/')
    dishes = {
        'disliked_1hr': Dish.objects.create(restaurant=res, title='disliked_1hr',
                                            firebase_id='a'),
        'liked': Dish.objects.create(restaurant=res, title='liked', firebase_id='b'),
        'unseen': Dish.objects.create(restaurant=res, title='unseen',
                                      firebase_id='c'),
        'disliked_1dy': Dish.objects.create(restaurant=res, title='disliked_1dy',
                                            firebase_id='d'),
        'u1_liked': Dish.objects.create(restaurant=res, title='u1_liked',
                                        firebase_id='e')
    }
    return res, dishes

class LoggedInTestcase(object):
    def setUp_session(self):
        users = [
            User.objects.create(email='test@test.test', username='test',
                                first_name='tob')
        ]
        self.c = Client()
        self.c.force_login(users[0])


class TestDishViewSet(TestCase):
    fixtures = []
    fixture_created = False

    def setUp(self):
        self.create_fixture()

    def create_fixture(self):
        res, self.dishes = setupDishesAndRestaurants()
        users = [
            User.objects.create(email='test@test.test', username='test',
                                first_name='tob'),
            User.objects.create(email='tes1t@test.test', username='test1',
                                first_name='gob'),
            User.objects.create(email='tes2t@test.test', username='test2',
                                first_name='nob'),
        ]
        profiles = [
            Profile.objects.create(user=users[0]),
            Profile.objects.create(user=users[1]),
            Profile.objects.create(user=users[2]),
        ]
        one_hr = timezone.now() - timedelta(minutes=30)  # Now 30m for 1hr freshness.
        three_hr = timezone.now() - timedelta(hours=3)
        day = timezone.now() - timedelta(hours=24)

        turn_off_auto_now(Like, 'updated')
        turn_off_auto_now_add(Like, 'created')
        self.likes = {
            'disliked_1hr': Like.objects.create(user=users[0],
                                                dish=self.dishes['disliked_1hr'],
                                                created=one_hr, updated=one_hr),
            'liked': Like.objects.create(user=users[0], dish=self.dishes['liked'],
                                         created=three_hr, updated=three_hr,
                                         did_like=True),
            'disliked_1dy': Like.objects.create(user=users[0],
                                                dish=self.dishes['disliked_1dy'],
                                                created=day, updated=day),
            'u1_liked': Like.objects.create(user=users[1], dish=self.dishes['u1_liked'],
                                            created=day, updated=three_hr, did_like=True)
        }
        self.users = users

    def get_titles_arrs(self):
        dishes = Dish.objects.all()
        dishes_excl = dishes.not_liked(self.users[0]).fresh(self.users[0])
        titles = [(dish.title, ) for dish in dishes]
        excl_titles = [(dish.title, ) for dish in dishes_excl]
        return titles, excl_titles

    def test_exclude_disliked_1hr(self):
        """Should exclude a dish the user disliked 1 hr ago."""
        titles, excl_titles = self.get_titles_arrs()
        #  print('Only disliked_1hr and unseen:', excl_titles)
        self.assertNotIn('disliked_1hr', [t[0] for t in excl_titles])

    def test_exclude_liked_3hrs(self):
        """Should exclude a dish the user liked 3 hrs ago."""
        titles, excl_titles = self.get_titles_arrs()
        self.assertNotIn('liked', [t[0] for t in excl_titles])

    def test_return_never_seen(self):
        """Should return a dish the user has never seen."""
        titles, excl_titles = self.get_titles_arrs()
        self.assertIn('unseen', [t[0] for t in titles])

    def test_return_disliked_1dy(self):
        """Should return a dish the user disliked yesterday."""
        titles, excl_titles = self.get_titles_arrs()
        self.assertIn('disliked_1dy', [t[0] for t in titles])

    def test_u1_return_liked_by_u0(self):
        """u1 query should return all dishes interacted with by u0."""
        res = Dish.objects.not_liked(self.users[1]).fresh(self.users[1])
        arr = [d.title for d in res]
        #  print('All dishes except u1_liked:', arr)
        self.assertIn('disliked_1hr', arr)
        self.assertIn('disliked_1dy', arr)
        self.assertIn('unseen', arr)
        self.assertIn('liked', arr)
        self.assertNotIn('u1_liked', arr)

    def test_u2_return_all(self):
        """u2 query should return all dishes despite no likes."""
        res = Dish.objects.not_liked(self.users[2]).fresh(self.users[2])
        arr = [d.title for d in res]
        for k, d in self.dishes.items():
            self.assertIn(k, arr)

    def test_not_liked(self):
        """Should remove liked dishes from query."""
        r1 = Dish.objects.not_liked(self.users[0])
        self.prepare_and_assert_dishes(r1, 'liked')
        r2 = Dish.objects.not_liked(self.users[1])
        self.prepare_and_assert_dishes(r2, 'u1_liked')
        r3 = Dish.objects.not_liked(self.users[2])
        for k, v in self.dishes.items():
            self.assertIn(k, [d.title for d in r3])

    def test_fresh(self):
        """Should remove dishes recently disliked."""
        self.prepare_and_assert_dishes(Dish.objects.fresh(self.users[0]), 'disliked_1hr')
        self.prepare_and_assert_dishes(Dish.objects.fresh(self.users[1]), '')
        self.prepare_and_assert_dishes(Dish.objects.fresh(self.users[2]), '')

    def prepare_and_assert_dishes(self, qs, exclude_target):
        arr1 = [d.title for d in qs]
        for k, v in self.dishes.items():
            if k == exclude_target:
                self.assertNotIn(k, arr1)
            else:
                self.assertIn(k, arr1)


class TestAuthentication(TestCase):
    def setUp(self):
        users = [
            User.objects.create(email='test@test.test', username='test',
                                first_name='tob'),
            User.objects.create(email='tes1t@test.test', username='test1',
                                first_name='gob'),
            User.objects.create(email='tes2t@test.test', username='test2',
                                first_name='nob'),
        ]
        profiles = [
            Profile.objects.create(user=users[0], firebase_id='111'),
            Profile.objects.create(user=users[1], firebase_id='112'),
            Profile.objects.create(user=users[2], firebase_id='113'),
        ]
        self.photo_url = 'https://scontent.xx.fbcdn.net/v/t1.0-1/s100x100/'
        self.photo_url += '1379841_10150004552801901_469209496895221757_n'
        self.photo_url += '.jpg?oh=a082e0f02afca5f03ab570c71732b870&oe=59B30197'
        self.tokens = [{
            'sub': 'EYjkm7sX2pWVHnA56YD3MykTU4I2',
            'aud': 'feedmee-appsppl-dev', 'exp': 1496414513,
            'picture': self.photo_url,
            'auth_time': 1496410911, 'iat': 1496410913,
            'user_id': 'EYjkm7sX2pWVHnA56YD3MykTU4I2',
            'firebase': {
                'sign_in_provider': 'facebook.com',
                'identities': {
                    'facebook.com': ['105626553369738']
                }
            },
            'name': 'Karen Alagfgahabefh Sharpestein',
            'iss': 'https://securetoken.google.com/feedmee-appsppl-dev'
        }]
        self.auth = FirebaseJWTBackend()
        self.users = users
        self.profiles = profiles

    def test_get_user(self):
        usr0 = self.auth._get_user('111')
        self.assertEqual(usr0, self.users[0])
        usr1 = self.auth._get_user('test1')
        self.assertEqual(usr1, self.users[1])
        with self.assertRaises(User.DoesNotExist):
            self.auth._get_user('123')

    def test_create_user(self):
        user, profile = self.auth._create_user(self.tokens[0])
        self.assertEqual(user.username, 'EYjkm7sX2pWVHnA56YD3MykTU4I2')
        self.assertEqual(user.email, '')
        self.assertEqual(user.first_name, 'Karen')
        self.assertEqual(user.last_name, 'Sharpestein')
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.provider, 'facebook.com')
        self.assertEqual(profile.firebase_id, 'EYjkm7sX2pWVHnA56YD3MykTU4I2')
        self.assertEqual(profile.fb_id, '105626553369738')
        self.assertEqual(profile.photo_url, self.photo_url)


class TestApiEndpoints(TestCase, LoggedInTestcase):
    def setUp(self):
        self.setUp_session()
        res, self.dishes = setupDishesAndRestaurants()

    def test_dish_feed(self):
        res = self.c.get('/api/dishes/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"count":5', count=1)
        # self.assertJSONEqual(res.content, )

    def test_saved_dishes(self):
        res = self.c.get('/api/dishes/', {'saved': 'true'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"count":0', count=1)

    def test_saved_dishes_count(self):
        res = self.c.get('/api/dishes/', {'saved': 'true', 'count': 'true'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"count":0', count=1)

    def test_like_dish(self):
        dish_id = list(self.dishes.values())[0].id
        res = self.c.post('/api/likes/dishes/', {'did_like': True, 'dish_id': dish_id})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"created":true', count=1)
        self.assertContains(res, '"success":true', count=1)
        res2 = self.c.get('/api/dishes/')
        self.assertEqual(res2.status_code, 200)
        self.assertContains(res2, '"count":4', count=1)

    def test_view_dish(self):
        dish_id = list(self.dishes.values())[0].id
        res = self.c.post('/api/views/dishes/', {'dish_id': dish_id})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"success":true', count=1)

    def test_like_dish_old_route(self):
        dish_id = list(self.dishes.values())[0].id
        res = self.c.post('/api/likes/', {'did_like': True, 'dish_id': dish_id})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"created":true', count=1)
        self.assertContains(res, '"success":true', count=1)
        res2 = self.c.get('/api/dishes/')
        self.assertEqual(res2.status_code, 200)
        self.assertContains(res2, '"count":4', count=1)

    def test_view_dish_old_route(self):
        dish_id = list(self.dishes.values())[0].id
        res = self.c.post('/api/views/', {'dish_id': dish_id})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"success":true', count=1)


class TestRecipeApi(TestCase, LoggedInTestcase):
    fixtures = ['fixtures/recipes_with_duplicates2.json', ]

    def setUp(self):
        self.setUp_session()

    def test_recipe_get(self):
        res = self.c.get('/api/recipes/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"count":10', count=1)

    def test_recipe_keywords(self):
        res = self.c.get('/api/recipes/', {'keywords': 'vegetarian'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"count":1', count=1)
        res = self.c.get('/api/recipes/', {'keywords': 'vegan'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"count":0', count=1)

    def test_recipe_tags(self):
        res = self.c.get('/api/recipes/', {'tags': 'Bacon'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"count":1', count=1)

    def test_recipe_difficulty(self):
        res = self.c.get('/api/recipes/', {'difficulty': 'dt'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"count":1', count=1)

    def test_recipe_ingredient(self):
        res = self.c.get('/api/recipes/', {'ingredients': 'Chimichangas'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"count":1', count=1)

    def test_like_recipe(self):
        recipe_id = list(Recipe.objects.all().values())[0]['id']
        res = self.c.post('/api/likes/recipes/', {'did_like': True, 'recipe_id': recipe_id})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"created":true', count=1)
        self.assertContains(res, '"success":true', count=1)
        res2 = self.c.get('/api/recipes/')
        self.assertEqual(res2.status_code, 200)
        self.assertContains(res2, '"count":9', count=1)

    def test_view_recipe(self):
        recipe_id = list(Recipe.objects.all().values())[0]['id']
        res = self.c.post('/api/views/recipes/', {'recipe_id': recipe_id})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"success":true', count=1)

    def test_saved_recipes(self):
        recipe_id = list(Recipe.objects.all().values())[3]['id']
        res = self.c.post('/api/likes/recipes/', {'did_like': True, 'recipe_id': recipe_id})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"created":true', count=1)
        self.assertContains(res, '"success":true', count=1)
        res2 = self.c.get('/api/recipes/', {'saved': 'true'})
        self.assertEqual(res2.status_code, 200)
        self.assertContains(res2, '"count":1', count=1)

    def test_saved_recipes_count(self):
        recipe_id = list(Recipe.objects.all().values())[3]['id']
        self.c.post('/api/likes/recipes/', {'did_like': True, 'recipe_id': recipe_id})
        res = self.c.get('/api/recipes/', {'saved': 'true', 'count': 'true'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"count":1', count=1)


class TestRecipeCollectionApi(TestCase, LoggedInTestcase):
    fixtures = ['fixtures/keywords.json',
                'fixtures/recipes_from_dev.json',
                'fixtures/recipe_collections.json']

    def setUp(self):
        self.setUp_session()

    def test_list_collections(self):
        res = self.c.get('/api/recipes-collections/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"count":3', count=1)

    def test_retrieve_collection(self):
        res = self.c.get('/api/recipes-collections/no-cook-recipes/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"name":"No cook recipes"', count=1)


class TestRecipeRatingApi(TestCase, LoggedInTestcase):
    fixtures = ['fixtures/recipes_with_duplicates2.json', ]

    def setUp(self):
        self.setUp_session()

    def test_get_rating(self):
        res = self.c.get('/api/recipes/10/ratings/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"user_rating":0', count=1)
        self.assertContains(res, '"ratings_count":0', count=1)
        self.assertContains(res, '"rating":"0.0"', count=1)

    def test_get_rating_anonymous(self):
        res = Client().get('/api/recipes/10/ratings/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"user_rating":0', count=1)
        self.assertContains(res, '"ratings_count":0', count=1)
        self.assertContains(res, '"rating":"0.0"', count=1)

    def test_set_rating(self):
        res = self.c.post('/api/recipes/10/ratings/', data={'rating': 4})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"success":true', count=1)
        res2 = self.c.get('/api/recipes/10/ratings/', count=1)
        self.assertContains(res2, '"user_rating":4', count=1)
        self.assertContains(res2, '"ratings_count":1', count=1)
        self.assertContains(res2, '"rating":"4.0"', count=1)

    def test_set_rating_invalid_recipe(self):
        res = self.c.post('/api/recipes/11111111/ratings/', data={'rating': 4})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"success":false', count=1)


class TestGeocodeApi(TestCase, LoggedInTestcase):
    def setUp(self):
        self.setUp_session()

    def test_geocode_address(self):
        res = self.c.get('/api/geocode/', data={'address': '474 Murray st, Perth, Western Australia'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"suburb":["Perth"]', count=1)
        self.assertContains(res, '"longitude":115.8518421', count=1)
        self.assertContains(res, '"latitude":-31.9502606', count=1)


class TestSuburbList(TestCase, LoggedInTestcase):
    fixtures = ['fixtures/cuisines.json', 'fixtures/blogs.json',
                'fixtures/highlights.json', 'fixtures/keywords.json',
                'fixtures/dishes_restaurants_subset.json']

    def setUp(self):
        self.setUp_session()

    def test_suburb_list(self):
        res = self.c.get('/api/suburbs/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"count":21', count=1)
        self.assertContains(res, '"Northbridge"', count=1)
        self.assertContains(res, '"Perth CBD"', count=1)
        self.assertContains(res, '"Docklands"', count=1)
        self.assertContains(res, '"Brunswick"', count=1)
        self.assertContains(res, '"Southbank"', count=1)


class TestSearchTerms(TestCase, LoggedInTestcase):
    fixtures = ['fixtures/cuisines.json', 'fixtures/blogs.json',
                'fixtures/highlights.json', 'fixtures/keywords.json',
                'fixtures/dishes_restaurants_subset.json',
                'fixtures/recipes_with_duplicates2.json']

    def setUp(self):
        self.setUp_session()

    def test_search_terms(self):
        res = self.c.get('/api/search-terms/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"count":168', count=1)
        self.assertContains(res, '"keywords":[', count=1)
        self.assertContains(res, '"highlights":[', count=1)
        self.assertContains(res, '"tags":[', count=1)
        self.assertContains(res, '"ingredients":[', count=1)


class TestShoppingLists(TestCase, LoggedInTestcase):
    fixtures = ['fixtures/keywords.json', 'fixtures/recipes_with_duplicates2.json']

    def setUp(self):
        self.setUp_session()

    def test_send_shopping_list(self):
        res = self.c.post('/api/shopping-lists/', json.dumps({
            'shopping_list': (
                {
                    'recipe_id': 2,
                    'ingredient': 'Sausages',
                    'ticked': False
                },
                {
                    'recipe_id': 2,
                    'ingredient': 'Eschallots',
                    'ticked': True
                },
                {
                    'custom_item': True,
                    'content': 'Toilet paper',
                    'ticked': False
                },
                {
                    'custom_item': True,
                    'content': 'Tissues',
                    'ticked': True
                },
            )
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"success":true', count=1)
        saus = Item.objects.get(ingredient='Sausages')
        self.assertFalse(saus.ticked)
        self.assertEqual(saus.recipe_id, 2)
        esch = Item.objects.get(ingredient='Eschallots')
        self.assertTrue(esch.ticked)
        self.assertEqual(esch.recipe_id, 2)
        tp = CustomItem.objects.get(content='Toilet paper')
        self.assertFalse(tp.ticked)
        tis = CustomItem.objects.get(content='Tissues')
        self.assertTrue(tis.ticked)
        sl = ShoppingList.objects.all()[0]
        self.assertEqual(sl.items.count(), 2)
        self.assertEqual(sl.custom_items.count(), 2)



class TestFulfilmentEventPost(TestCase, LoggedInTestcase):
    fixtures = ['fixtures/cuisines.json', 'fixtures/blogs.json',
                'fixtures/highlights.json', 'fixtures/keywords.json',
                'fixtures/dishes_restaurants_subset.json']

    def setUp(self):
        self.setUp_session()

    def test_fe_delivery(self):
        pdata = {'delivery_type': 'ubereats', 'dish_id': 3340}
        res = self.c.post('/api/fulfilment-events/', pdata)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"success":true', count=1)
        self.assertEqual(FulfilmentEvent.objects.all().count(), 1)
        pdata = {'delivery_type': 'deliveroo', 'dish_id': 3340}
        res = self.c.post('/api/fulfilment-events/', pdata)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"success":true', count=1)
        self.assertEqual(FulfilmentEvent.objects.all().count(), 2)

    def test_fe_booking(self):
        pdata = {'booking_type': 'quandoo', 'dish_id': 3340}
        res = self.c.post('/api/fulfilment-events/', pdata)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"success":true', count=1)
        self.assertEqual(FulfilmentEvent.objects.all().count(), 1)
        pdata = {'booking_type': 'quandoo', 'dish_id': 3340}
        res = self.c.post('/api/fulfilment-events/', pdata)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '"success":true', count=1)
        self.assertEqual(FulfilmentEvent.objects.all().count(), 2)

    def test_fe_errors(self):
        pdata = {'booking_type': 'quandoo', 'dish_id': 1}
        res = self.c.post('/api/fulfilment-events/', pdata)
        self.assertEqual(res.status_code, 400)
        self.assertContains(res, '"success":false', count=1, status_code=400)
        self.assertContains(res, '"created":false', count=1, status_code=400)
        self.assertContains(res, '"Error":"Dish not found"',
                            count=1, status_code=400)

        pdata = {'delivery_type': 'an invalid provider', 'dish_id': 3340}
        res = self.c.post('/api/fulfilment-events/', pdata)
        self.assertEqual(res.status_code, 400)
        self.assertContains(res, '"success":false', count=1, status_code=400)
        self.assertContains(res, '"created":false', count=1, status_code=400)
        self.assertContains(res, '"Error":"Delivery Provider not found"',
                            count=1, status_code=400)

        pdata = {'booking_type': 'an invalid provider', 'dish_id': 3340}
        res = self.c.post('/api/fulfilment-events/', pdata)
        self.assertEqual(res.status_code, 400)
        self.assertContains(res, '"success":false', count=1, status_code=400)
        self.assertContains(res, '"created":false', count=1, status_code=400)
        self.assertContains(res, '"Error":"Booking Provider not found"',
                            count=1, status_code=400)

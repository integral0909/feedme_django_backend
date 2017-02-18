from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings
import wget
import datetime


def prepare_vars(table, fb_url, key):
    table_url = '{}{}.json?{}'.format(fb_url, table, key)
    datestr = datetime.date.today().strftime('%d%m%y')
    local_path = '{}{}-{}.json'.format(settings.TMP_PATH, table, datestr)
    if table == 'restaurantBlogs':
        django_table = 'restaurant_blogs'
    else:
        django_table = table
    return (table_url, datestr, local_path, django_table)


class Command(BaseCommand):
    """
    Accept 0 or more tables to migrate from Firebase to Django.

    If no tables are provided, all tables will be migrated.
    Requires an api key and firebase db name.
    """
    def add_arguments(self, parser):
        tables = ['restaurants', 'dishes', 'blogs', 'restaurantBlogs', 'users', 'likes']
        parser.add_argument('tables', nargs='*', type=str, default=tables)
        parser.add_argument('--key', help='API Key for Firebase DB')
        parser.add_argument('--fbdb', help='Path to Firebase DB')

    def handle(self, *args, **options):
        fb_url = 'https://{}.firebaseio.com/'.format(options['fbdb'])
        key = "auth={}".format(options['key'])
        for table in options['tables']:
            table_url, datestr, local_path, django_table = prepare_vars(table,
                                                                        fb_url,
                                                                        key)
            filepath = wget.download(table_url, local_path)
            call_command('load_firebase_dump', django_table, filepath)

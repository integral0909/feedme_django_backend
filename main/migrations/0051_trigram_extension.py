from django.db import migrations, models
from django.contrib.postgres.operations import TrigramExtension

class Migration(migrations.Migration):
    dependencies = [
       ('main', '0050_auto_20170809_1629')
    ]

    operations = [
        TrigramExtension(),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-11 11:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_keyword_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='keyword',
            name='slug',
            field=models.SlugField(help_text='A slug helps query via url', max_length=255, unique=True),
        ),
    ]

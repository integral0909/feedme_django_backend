# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-18 13:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_auto_20170218_0756'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryprovider',
            name='title',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]

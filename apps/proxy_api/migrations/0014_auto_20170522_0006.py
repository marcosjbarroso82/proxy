# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-22 00:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proxy_api', '0013_auto_20170522_0004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accesspoint',
            name='response',
            field=models.TextField(blank=True, null=True),
        ),
    ]

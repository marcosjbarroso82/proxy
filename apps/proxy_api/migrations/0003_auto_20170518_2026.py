# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-18 20:26
from __future__ import unicode_literals

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('proxy_api', '0002_auto_20170518_1859'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accesspoint',
            name='response',
            field=jsonfield.fields.JSONField(blank=True, default=dict, null=True),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-04 17:24
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('proxy_api', '0026_auto_20170604_1620'),
    ]

    operations = [
        migrations.RenameField(
            model_name='proxyapp',
            old_name='attributes',
            new_name='app_variables',
        ),
    ]

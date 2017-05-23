# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-22 23:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('proxy_api', '0019_remove_incommingrequest_payload'),
    ]

    operations = [
        migrations.AddField(
            model_name='incommingrequest',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='incommingrequest',
            name='log',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]

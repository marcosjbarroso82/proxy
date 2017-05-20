# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-20 18:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proxy_api', '0003_auto_20170518_2026'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProxyApp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
                ('root_path', models.CharField(max_length=200, unique=True)),
            ],
        ),
    ]
# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-23 00:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proxy_api', '0020_auto_20170522_2309'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReusableApiRequestVariable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('jinja', 'jinja')], max_length=20)),
                ('required', models.BooleanField(default=False)),
                ('key', models.CharField(max_length=20)),
                ('value', models.TextField()),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variables', to='proxy_api.ReusableApiRequest')),
            ],
        ),
    ]
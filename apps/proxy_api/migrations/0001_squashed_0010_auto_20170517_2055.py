# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-17 21:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    replaces = [('proxy_api', '0001_initial'), ('proxy_api', '0002_auto_20170517_1950'), ('proxy_api', '0003_auto_20170517_2021'), ('proxy_api', '0004_auto_20170517_2035'), ('proxy_api', '0005_auto_20170517_2041'), ('proxy_api', '0006_auto_20170517_2044'), ('proxy_api', '0007_auto_20170517_2045'), ('proxy_api', '0008_auto_20170517_2051'), ('proxy_api', '0009_auto_20170517_2052'), ('proxy_api', '0010_auto_20170517_2055')]

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccessPoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('log', models.TextField(blank=True, default='', null=True)),
                ('pre_request_operation', models.TextField(blank=True, null=True)),
                ('post_request_operation', models.TextField(blank=True, help_text='available variables: request, context, state, response', null=True)),
                ('name', models.CharField(max_length=20, unique=True)),
                ('method', models.CharField(choices=[('get', 'get'), ('post', 'post'), ('put', 'put'), ('patch', 'patch'), ('delete', 'delete'), ('options', 'options')], max_length=10)),
                ('slug', models.SlugField()),
                ('path', models.CharField(help_text='Ex: ".*"', max_length=200)),
                ('state_condition', models.CharField(blank=True, help_text='state.counter >= 13 # avalidation that returns True', max_length=100, null=True)),
                ('response', jsonfield.fields.JSONField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AccessPointEnvironment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('log', models.TextField(blank=True, default='', null=True)),
                ('pre_request_operation', models.TextField(blank=True, null=True)),
                ('post_request_operation', models.TextField(blank=True, help_text='available variables: request, context, state, response', null=True)),
                ('name', models.CharField(max_length=20, unique=True)),
                ('state_hash_id', models.CharField(blank=True, help_text='{{payload.entry.0.messaging.0.sender.id}}', max_length=50, null=True)),
                ('value', jsonfield.fields.JSONField(blank=True, default=dict, null=True)),
                ('root_path', models.CharField(default='', max_length=200, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AccessPointRequestExecution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('log', models.TextField(blank=True, default='', null=True)),
                ('request_definition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proxy_api.AccessPoint')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AccessPointReusableRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('log', models.TextField(blank=True, default='', null=True)),
                ('pre_request_operation', models.TextField(blank=True, null=True)),
                ('post_request_operation', models.TextField(blank=True, help_text='available variables: request, context, state, response', null=True)),
                ('condition', models.TextField(blank=True, default='')),
                ('params', models.TextField(blank=True, default='')),
                ('access_point_order', models.PositiveIntegerField(db_index=True, default=0, editable=False)),
                ('access_point', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reusable_requests', to='proxy_api.AccessPoint')),
            ],
            options={
                'ordering': ['access_point_order'],
            },
        ),
        migrations.CreateModel(
            name='RequestState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('log', models.TextField(blank=True, default='', null=True)),
                ('hash_id', models.CharField(max_length=50)),
                ('value', jsonfield.fields.JSONField(blank=True, default=dict, help_text='jinja. Available vars: ', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReusableApiRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('log', models.TextField(blank=True, default='', null=True)),
                ('pre_request_operation', models.TextField(blank=True, null=True)),
                ('post_request_operation', models.TextField(blank=True, help_text='available variables: request, context, state, response', null=True)),
                ('name', models.CharField(max_length=20, unique=True)),
                ('method', models.CharField(choices=[('get', 'get'), ('post', 'post'), ('put', 'put'), ('patch', 'patch'), ('delete', 'delete'), ('options', 'options')], max_length=10)),
                ('url', models.CharField(max_length=500)),
                ('payload', jsonfield.fields.JSONField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReusableApiRequestExecution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('log', models.TextField(blank=True, default='', null=True)),
                ('access_point_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reusable_request_executions', to='proxy_api.AccessPointRequestExecution')),
                ('request_definition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='request_executions', to='proxy_api.ReusableApiRequest')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='accesspointreusablerequest',
            name='request_definition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proxy_api.ReusableApiRequest'),
        ),
        migrations.AddField(
            model_name='accesspointrequestexecution',
            name='state',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='proxy_api.RequestState'),
        ),
        migrations.AddField(
            model_name='accesspoint',
            name='env',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proxy_api.AccessPointEnvironment'),
        ),
        migrations.AlterField(
            model_name='accesspoint',
            name='slug',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='accesspointreusablerequest',
            name='params',
            field=jsonfield.fields.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='accesspointreusablerequest',
            name='params',
            field=jsonfield.fields.JSONField(default={}),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='accesspointreusablerequest',
            name='params',
            field=jsonfield.fields.JSONField(default={}),
        ),
        migrations.AlterField(
            model_name='accesspointreusablerequest',
            name='params',
            field=jsonfield.fields.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='accesspointreusablerequest',
            name='params',
            field=jsonfield.fields.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AlterField(
            model_name='accesspoint',
            name='response',
            field=jsonfield.fields.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AlterField(
            model_name='reusableapirequest',
            name='payload',
            field=jsonfield.fields.JSONField(blank=True, default=dict, null=True),
        ),
    ]

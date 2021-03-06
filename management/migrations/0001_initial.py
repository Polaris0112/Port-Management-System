# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-10 09:15
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ipaddr', models.GenericIPAddressField(protocol='IPv4')),
                ('hostname', models.CharField(max_length=128)),
                ('type', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='MyUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nickname', models.CharField(max_length=16)),
                ('permission', models.IntegerField(default=2)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Port',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ipaddr', models.GenericIPAddressField(protocol='IPv4')),
                ('port', models.IntegerField()),
                ('acceptip', models.CharField(default='0.0.0.0', max_length=128)),
                ('record_id', models.CharField(default='record', max_length=128, unique=True)),
                ('usage', models.CharField(max_length=128)),
                ('protocol', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_name', models.CharField(max_length=128)),
                ('port', models.IntegerField()),
                ('protocol', models.CharField(max_length=128)),
                ('usage', models.CharField(max_length=128)),
            ],
        ),
    ]

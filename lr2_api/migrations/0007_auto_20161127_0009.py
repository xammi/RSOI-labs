# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-26 21:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lr2_api', '0006_auto_20161127_0004'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='refreshtoken',
            name='app',
        ),
        migrations.RemoveField(
            model_name='refreshtoken',
            name='user',
        ),
        migrations.AddField(
            model_name='refreshtoken',
            name='access_token',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='lr2_api.AccessToken'),
            preserve_default=False,
        ),
    ]

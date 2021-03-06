# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-26 21:04
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lr2_api', '0005_auto_20161126_1510'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=100, verbose_name='Access Token')),
                ('expires', models.DateTimeField(verbose_name='Истекает в')),
            ],
            options={
                'verbose_name_plural': 'Access Tokens',
                'verbose_name': 'Access Token',
            },
        ),
        migrations.CreateModel(
            name='RefreshToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=100, verbose_name='Refresh Token')),
            ],
            options={
                'verbose_name_plural': 'Refresh Tokens',
                'verbose_name': 'Refresh Token',
            },
        ),
        migrations.AlterUniqueTogether(
            name='application',
            unique_together=set([('client_id', 'client_secret')]),
        ),
        migrations.AddField(
            model_name='refreshtoken',
            name='app',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lr2_api.Application'),
        ),
        migrations.AddField(
            model_name='refreshtoken',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_refresh_tokens', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='accesstoken',
            name='app',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lr2_api.Application'),
        ),
        migrations.AddField(
            model_name='accesstoken',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_tokens', to=settings.AUTH_USER_MODEL),
        ),
    ]

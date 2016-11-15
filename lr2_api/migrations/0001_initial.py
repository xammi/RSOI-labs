# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-15 12:35
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import lr2_api.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('first_name', models.CharField(blank=True, max_length=30, null=True, verbose_name='Имя')),
                ('last_name', models.CharField(blank=True, max_length=60, null=True, verbose_name='Фамилия')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Персонал?')),
                ('is_active', models.BooleanField(default=False, verbose_name='Активен?')),
                ('access_token', models.CharField(blank=True, max_length=100, null=True, verbose_name='Токен доступа')),
                ('expires_in', models.PositiveIntegerField(blank=True, null=True, verbose_name='Время действия токена')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Пользователь',
                'verbose_name_plural': 'пользователи',
            },
            managers=[
                ('objects', lr2_api.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Название')),
                ('country', models.CharField(max_length=200, verbose_name='Страна')),
                ('city', models.CharField(blank=True, max_length=200, null=True, verbose_name='Город')),
                ('rating', models.PositiveSmallIntegerField(blank=True, choices=[(0, 'Отвратительно'), (1, 'Плохо'), (2, 'Так себе'), (3, 'Хорошо'), (4, 'Круто')], null=True, verbose_name='Общий рейтинг')),
            ],
            options={
                'verbose_name': 'Достопримечательность',
                'verbose_name_plural': 'достопримечательности',
            },
        ),
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('price', models.PositiveIntegerField(verbose_name='Стоимость')),
                ('depart_date', models.DateTimeField(blank=True, null=True, verbose_name='Дата выезда')),
                ('arrive_date', models.DateTimeField(blank=True, null=True, verbose_name='Дата окончания')),
            ],
            options={
                'verbose_name': 'Маршрут',
                'verbose_name_plural': 'маршруты',
            },
        ),
        migrations.CreateModel(
            name='RouteUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payed', models.BooleanField(default=False, verbose_name='Оплачено?')),
                ('route', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lr2_api.Route')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TravelCompany',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abbreviation', models.CharField(max_length=5, unique=True, verbose_name='Сокращение')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('info', models.TextField(blank=True, null=True, verbose_name='Информация о компании')),
            ],
            options={
                'verbose_name': 'Тур. Компания',
                'verbose_name_plural': 'тур. компании',
            },
        ),
        migrations.AddField(
            model_name='route',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='lr2_api.TravelCompany', verbose_name='Исполнитель'),
        ),
        migrations.AddField(
            model_name='route',
            name='locations',
            field=models.ManyToManyField(to='lr2_api.Location', verbose_name='Что посещаем?'),
        ),
        migrations.AddField(
            model_name='route',
            name='users',
            field=models.ManyToManyField(through='lr2_api.RouteUser', to=settings.AUTH_USER_MODEL, verbose_name='Группа'),
        ),
    ]

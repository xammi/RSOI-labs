from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields['is_active'] = True
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'пользователи'

    email = models.EmailField(verbose_name='Email', unique=True)
    first_name = models.CharField(verbose_name='Имя', null=True, blank=True, max_length=30)
    last_name = models.CharField(verbose_name='Фамилия', null=True, blank=True, max_length=60)

    is_staff = models.BooleanField(verbose_name='Персонал?', default=False)
    is_active = models.BooleanField(verbose_name='Активен?', default=False)

    access_token = models.CharField(verbose_name='Токен доступа', max_length=100, blank=True, null=True)
    expires_in = models.PositiveIntegerField(verbose_name='Время действия токена', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_full_name(self):
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return ' '.join(parts)

    def get_short_name(self):
        return '{0}'.format(self.email)

    def __str__(self):
        return '{0}'.format(self.email)

    def as_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'is_staff': self.is_staff,
            'companies': [
                company.as_dict() for company in self.travelcompany_set.all()
            ]
        }


class Location(models.Model):
    class Meta:
        verbose_name = 'Достопримечательность'
        verbose_name_plural = 'достопримечательности'

    name = models.CharField(verbose_name='Название', max_length=200, unique=True)
    country = models.CharField(verbose_name='Страна', max_length=200)
    city = models.CharField(verbose_name='Город', max_length=200, blank=True, null=True)
    rating = models.IntegerField(verbose_name='Общий рейтинг', blank=True, null=True)

    def __str__(self):
        return self.name

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'country': self.country,
            'city': self.city if self.city else None,
            'rating': self.rating if self.rating else None
        }


class TravelCompany(models.Model):
    class Meta:
        verbose_name = 'Тур. Компания'
        verbose_name_plural = 'тур. компании'

    abbreviation = models.CharField(verbose_name='Сокращение', max_length=5, unique=True)
    name = models.CharField(verbose_name='Название', max_length=200)
    info = models.TextField(verbose_name='Информация о компании', blank=True, null=True)
    user = models.ForeignKey('User', verbose_name='Владелец', blank=True, null=True)

    def __str__(self):
        return self.abbreviation

    def as_dict(self):
        return {
            'id': self.id,
            'abbr': self.abbreviation,
            'name': self.name,
            'info': self.info if self.info else None,
            'owner': self.user if self.user else None
        }


class RouteUser(models.Model):
    class Meta:
        unique_together = ('route', 'user')

    route = models.ForeignKey('Route')
    user = models.ForeignKey('User')
    payed = models.BooleanField(verbose_name='Оплачено?', default=False)


class Route(models.Model):
    class Meta:
        verbose_name = 'Маршрут'
        verbose_name_plural = 'маршруты'

    name = models.CharField(verbose_name='Название', max_length=200)

    company = models.ForeignKey('TravelCompany', verbose_name='Исполнитель', blank=True, null=True)
    locations = models.ManyToManyField('Location', verbose_name='Что посещаем?')
    users = models.ManyToManyField('User', verbose_name='Группа', through='RouteUser')

    price = models.PositiveIntegerField(verbose_name='Стоимость')
    depart_date = models.DateTimeField(verbose_name='Дата выезда', blank=True, null=True)
    arrive_date = models.DateTimeField(verbose_name='Дата окончания', blank=True, null=True)

    def __str__(self):
        return self.name

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'company': self.company.as_dict() if self.company else None,
            'locations': [
                loc.as_dict() for loc in self.locations.all()
            ],
            'group': [
                {'id': user.id, 'name': user.get_full_name()} for user in self.users.filter(is_active=True)
            ],
            'departure': self.depart_date.isoformat() if self.depart_date else None,
            'arrival': self.arrive_date.isoformat() if self.arrive_date else None
        }

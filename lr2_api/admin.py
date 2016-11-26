from django.contrib import admin

from lr2_api.models import User, Location, TravelCompany, Route, Application


@admin.register(TravelCompany)
class TravelCompanyAdmin(admin.ModelAdmin):
    list_display = ('abbreviation', 'name')
    search_fields = ('name', 'info')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'city', 'rating')
    list_filter = ('country',)
    search_fields = ('name', 'city')
    ordering = ('name',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'company', 'depart_date', 'arrive_date')
    list_filter = ('company',)
    search_fields = ('name', 'price')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_filter = ('name', 'client_id', 'client_secret', 'redirect_uri')
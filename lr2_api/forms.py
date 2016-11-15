from django import forms

from lr2_api.models import Route


class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ('name', 'company', 'price', 'depart_date', 'arrive_date')

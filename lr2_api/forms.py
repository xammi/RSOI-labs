from django import forms

from lr2_api.models import Route, User


class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ('name', 'company', 'price', 'depart_date', 'arrive_date')


class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')

    def save(self, commit=True):
        instance = super(RegisterForm, self).save(commit=False)
        instance.set_password(self.cleaned_data.get('password'))
        if commit:
            instance.save()
        return instance

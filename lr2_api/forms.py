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


class AuthForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'password')


class AllowForm(forms.Form):
    allow = forms.BooleanField(required=False)
    redirect_uri = forms.CharField(widget=forms.HiddenInput())
    client_id = forms.CharField(widget=forms.HiddenInput())
    response_type = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data')
        if data and 'scopes' in data:
            data['scope'] = data['scopes']
        super().__init__(*args, **kwargs)


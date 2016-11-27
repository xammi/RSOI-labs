import base64
import random
import binascii
from datetime import timedelta
from urllib.parse import unquote_plus

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, RedirectView
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone

from lr2_api.base_views import JsonView, PaginateMixin, OAuthRequiredMixin
from lr2_api.forms import RouteForm, RegisterForm, AuthForm, AllowForm
from lr2_api.models import Location, TravelCompany, Route, User, Application, OAuthCode, RefreshToken, AccessToken


def generate_token(length=30, chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    rand = random.SystemRandom()
    return ''.join(rand.choice(chars) for _ in range(length))


class RegisterView(FormView):
    http_method_names = ['get', 'post']
    template_name = 'lr2_api/register_form.html'
    form_class = RegisterForm
    model = User

    def get_success_url(self):
        return reverse('api:authorize')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        return super(RegisterView, self).form_valid(form)


class LoginView(FormView):
    http_method_names = ['get', 'post']
    template_name = 'lr2_api/auth_form.html'
    form_class = AuthForm
    model = User

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        context['next_goal'] = self.request.GET.get('next')
        return context

    def post(self, request, *args, **kwargs):
        req_data = self.request.POST
        form = self.get_form(self.get_form_class())
        self.redirect_uri = req_data.get('next')

        email, password = req_data.get('email'), req_data.get('password')
        if not email or not password:
            form.add_error('email', 'Заполни данные')
            return super(LoginView, self).form_invalid(form)

        user = authenticate(email=email, password=password)
        if not user:
            form.add_error('email', 'Неверная пара email-пароль')
            return super(LoginView, self).form_invalid(form)

        login(self.request, user)
        return HttpResponseRedirect(self.redirect_uri)


class LogoutView(RedirectView):
    pattern_name = 'api:usual_login'

    def get(self, request, *args, **kwargs):
        logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)


class AuthorizeView(LoginRequiredMixin, FormView):
    http_method_names = ['get', 'post']
    template_name = 'lr2_api/allow_form.html'
    form_class = AllowForm

    client_app = None

    def get(self, request, *args, **kwargs):
        client_id = request.GET.get('client_id')
        response_type = request.GET.get('response_type')
        if not client_id or response_type.lower() != 'code':
            return HttpResponseBadRequest()

        client_app = Application.objects.filter(client_id=client_id).first()
        if not client_app:
            return HttpResponseBadRequest()

        past_codes = OAuthCode.objects.filter(user=request.user, app=client_app, expires__gt=timezone.now())
        if past_codes.exists():
            back_uri = self.create_code(client_app)
            return HttpResponseRedirect(back_uri)

        self.client_app = client_app
        return super(AuthorizeView, self).get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(AuthorizeView, self).get_form_kwargs()
        if 'data' not in kwargs:
            kwargs['data'] = {
                'client_id': self.client_app.client_id,
                'redirect_uri': self.client_app.redirect_uri,
                'response_type': 'code',
            }
        return kwargs

    def create_code(self, client_app):
        token = generate_token()
        expires = timezone.now() + timedelta(seconds=60)
        grant = OAuthCode(user=self.request.user, app=client_app, token=token, expires=expires)
        grant.save()
        return '{0}?code={1}'.format(client_app.redirect_uri, grant.token)

    def form_valid(self, form):
        allow = form.cleaned_data.get('allow')
        client_id = form.cleaned_data.get('client_id')
        client_app = Application.objects.filter(client_id=client_id).first()
        if not client_app:
            return HttpResponseBadRequest()

        back_uri = self.create_code(client_app) if allow else reverse('api:usual_login')
        return HttpResponseRedirect(back_uri)


class AccessTokenView(JsonView):
    http_method_names = ['post']

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(AccessTokenView, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def get_client(request):
        try:
            enc = request.encoding or 'utf-8'
        except AttributeError:
            enc = 'utf-8'
        auth_string = request.META.get('HTTP_AUTHORIZATION')
        auth_string = auth_string.split(' ', 1)[1]
        try:
            b64_dec = base64.b64decode(auth_string)
        except (TypeError, binascii.Error):
            return None
        try:
            auth_decoded = b64_dec.decode(enc)
        except UnicodeDecodeError:
            return None
        client_id, client_secret = map(unquote_plus, auth_decoded.split(':', 1))
        client_app = Application.objects.filter(client_id=client_id).first()
        if client_app and client_app.client_secret == client_secret:
            return client_app
        return None

    def save_token(self, token, request, client_app):
        refresh_token = request.POST.get('refresh_token')
        if refresh_token:
            # revoke old token
            rt = RefreshToken.objects.filter(token=refresh_token).first()
            if rt:
                rt.access_token.delete()
                rt.delete()

        expires = timezone.now() + timedelta(seconds=36000)
        access_token = AccessToken(app=client_app, user=request.grant_user, token=token['access_token'], expires=expires)
        access_token.save()
        refresh_token = RefreshToken(token=token['refresh_token'], access_token=access_token)
        refresh_token.save()

    def post(self, request, *args, **kwargs):
        grant_type = request.POST.get('grant_type')
        if grant_type.lower() != 'authorization_code':
            return HttpResponseBadRequest()

        code = request.POST.get('code')
        if not code:
            return HttpResponseBadRequest()

        client_app = self.get_client(request)
        grant = OAuthCode.objects.filter(app=client_app, token=code, expires__gt=timezone.now()).first()
        if not grant:
            return HttpResponseForbidden()

        request.grant_user = grant.user
        token = {
            'expires_in': 3600,
            'access_token': generate_token(),
            'refresh_token': generate_token(),
            'token_type': 'Bearer',
        }
        self.save_token(token, request, client_app)
        try:
            OAuthCode.objects.filter(token=code, app=client_app).delete()
        except Exception:
            pass
        return super(AccessTokenView, self).post(request, token=token, *args, **kwargs)

    def get_json_data(self, token, **kwargs):
        json = super(AccessTokenView, self).get_json_data(**kwargs)
        json.update(token)
        return json


class LocationsView(PaginateMixin, JsonView):
    http_method_names = ['get']
    model = Location
    data_key = 'locations'


class TravelCompaniesView(PaginateMixin, JsonView):
    http_method_names = ['get']
    model = TravelCompany
    data_key = 'companies'


class PersonalInfoView(OAuthRequiredMixin, JsonView):
    http_method_names = ['get']

    def get_json_data(self, user, **kwargs):
        return user.as_dict()


class MyRoutesView(OAuthRequiredMixin, PaginateMixin, JsonView):
    http_method_names = ['get']
    data_key = 'routes'

    def get_queryset(self, user, **kwargs):
        return user.route_set.all()


class RouteView(OAuthRequiredMixin, JsonView):
    http_method_names = ['get', 'post', 'patch']
    form_class = RouteForm

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            return super(RouteView, self).dispatch(request, *args, **kwargs)

        route = get_object_or_404(Route, id=kwargs.get('route_id'))
        user = kwargs.get('user')
        if user and route in user.route_set:
            return super(RouteView, self).dispatch(request, route=route, *args, **kwargs)

        return HttpResponseForbidden()

    def get(self, request, *args, **kwargs):
        json_data = kwargs.get('route').as_dict()
        return self.prepare_response(request, json_data=json_data, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        json_data = {'status': 'OK'}
        form = self.form_class(request.POST)
        if form.is_valid():
            ins = form.save()
        else:
            json_data = form.errors
        return self.prepare_response(request, json_data, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        json_data = {'status': 'OK'}
        form = self.form_class(request.PATCH, instance=kwargs.get('route'))
        if form.is_valid():
            ins = form.save()
        else:
            json_data = form.errors
        return self.prepare_response(request, json_data, *args, **kwargs)


class RouteLocationView(OAuthRequiredMixin, JsonView):
    http_method_names = ['post', 'delete']

    def dispatch(self, request, *args, **kwargs):
        route = get_object_or_404(Route, id=kwargs.get('route_id'))
        location = get_object_or_404(Location, id=kwargs.get('location_id'))

        user = kwargs.get('user')
        if user and route in user.route_set:
            return super(RouteLocationView, self).dispatch(request, route=route, location=location,
                                                           *args, **kwargs)
        return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        kwargs.get('route').locations.add(kwargs.get('location'))
        return super(RouteLocationView, self).post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        kwargs.get('route').locations.remove(kwargs.get('location'))
        return super(RouteLocationView, self).delete(request, *args, **kwargs)

    def get_json_data(self, **kwargs):
        return {'status': 'OK'}


class RouteRegisterView(OAuthRequiredMixin, JsonView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        route = get_object_or_404(Route, id=kwargs.get('route_id'))
        user = kwargs.get('user')
        if not user:
            return HttpResponseForbidden()

        if route not in user.route_set:
            user.route_set.add(route)
        return super(RouteRegisterView, self).post(request, *args, **kwargs)

    def get_json_data(self, **kwargs):
        return {'status': 'OK'}

import hashlib

from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.utils import timezone

from lr2_api.base_views import JsonView, PaginateMixin, LoginRequiredMixin
from lr2_api.forms import RouteForm, RegisterForm
from lr2_api.models import Location, TravelCompany, Route, User


class RegisterView(FormView):
    http_method_names = ['get', 'post']
    template_name = 'lr2_api/register_form.html'
    form_class = RegisterForm
    model = User

    def get_success_url(self):
        return reverse('api:authorize')

    @staticmethod
    def get_user_code(user, **kwargs):
        enc_email = str(user.email).encode('utf-8')
        enc_salt = str(settings.SECRET_KEY[:5]).encode('utf-8')
        return hashlib.sha1(enc_email + enc_salt).hexdigest()
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.code = self.get_user_code(user)[:100]
        user.save()
        return super(RegisterView, self).form_valid(form)


class AuthorizeView(TemplateView):
    http_method_names = ['get', 'post']
    template_name = 'lr2_api/auth_form.html'
    model = User

    def get_success_url(self, user, *args, **kwargs):
        client_id = kwargs.get('client_id')
        if client_id == settings.LR2_CLIENT_KEY:
            callback = settings.LR2_CALLBACK
            return callback + '?code=' + user.code
        raise Http404()

    def get(self, request, *args, **kwargs):
        client_id = request.GET.get('client_id')
        response_type = request.GET.get('response_type')
        if not client_id or response_type.lower() != 'code':
            return HttpResponseBadRequest()
        return super(AuthorizeView, self).get(request, client_id=client_id, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AuthorizeView, self).get_context_data(**kwargs)
        context['client_id'] = kwargs.get('client_id')
        return context

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        password = request.POST.get('password')
        client_id = request.POST.get('client_id')
        if not email or not password or not client_id:
            return HttpResponseBadRequest()

        user = authenticate(email=email, password=password)
        if user:
            login(self.request, user)
            return HttpResponseRedirect(self.get_success_url(user=user, client_id=client_id, **kwargs))
        else:
            context = {'error': 'Пользователь не существует'}
            return render(request, self.template_name, context)


class AccessTokenView(JsonView):
    http_method_names = ['post']

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(AccessTokenView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        grant_type = request.POST.get('grant_type')
        if grant_type.lower() != 'authorization_code':
            return HttpResponseBadRequest()

        code = request.POST.get('code')
        if not code:
            return HttpResponseForbidden()
        return super(AccessTokenView, self).post(request, code=code, *args, **kwargs)

    @staticmethod
    def get_access_token(code):
        enc_code = str(code).encode('utf-8')
        enc_salt = str(settings.SECRET_KEY[5:10]).encode('utf-8')
        return hashlib.sha1(enc_code + enc_salt).hexdigest()
    
    @staticmethod
    def get_expires(code, access_token):
        timestamp = timezone.now() + timezone.timedelta(minutes=3)
        return int(timestamp.strftime('%s'))

    @staticmethod
    def get_refresh_token(access_token, expires):
        enc_acct = str(access_token).encode('utf-8')
        enc_exp = str(expires).encode('utf-8')
        enc_salt = str(settings.SECRET_KEY[10:15]).encode('utf-8')
        return hashlib.sha1(enc_acct + enc_exp + enc_salt).hexdigest()

    def get_json_data(self, code, **kwargs):
        json_data = super(AccessTokenView, self).get_json_data(**kwargs)
        access_token = self.get_access_token(code)
        expires = self.get_expires(code, access_token)
        refresh_token = self.get_refresh_token(access_token, expires)

        User.objects.filter(code=code).update(access_token=access_token, expires_in=expires)

        json_data.update({
            'access_token': access_token,
            'expires': expires,
            'refresh_token': refresh_token,
        })
        return json_data


class LocationsView(PaginateMixin, JsonView):
    http_method_names = ['get']
    model = Location
    data_key = 'locations'


class TravelCompaniesView(PaginateMixin, JsonView):
    http_method_names = ['get']
    model = TravelCompany
    data_key = 'companies'


class PersonalInfoView(LoginRequiredMixin, JsonView):
    http_method_names = ['get']

    def get_json_data(self, user, **kwargs):
        return user.as_dict()


class MyRoutesView(LoginRequiredMixin, PaginateMixin, JsonView):
    http_method_names = ['get']
    data_key = 'routes'

    def get_queryset(self, user, **kwargs):
        return user.route_set.all()


class RouteView(LoginRequiredMixin, JsonView):
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


class RouteLocationView(LoginRequiredMixin, JsonView):
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


class RouteRegisterView(LoginRequiredMixin, JsonView):
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

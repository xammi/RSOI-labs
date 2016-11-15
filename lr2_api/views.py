from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from lr2_api.base_views import JsonView, PaginateMixin, LoginRequiredMixin
from lr2_api.models import Location, TravelCompany, Route


class IndexView(TemplateView):
    http_method_names = ['get']
    template_name = 'lr2_api/index.html'


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

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            return super(RouteView, self).dispatch(request, *args, **kwargs)

        route = get_object_or_404(Route, id=kwargs.get('route_id'))
        user = kwargs.get('user')
        if route in user.route_set:
            return super(RouteView, self).dispatch(request, route=route, *args, **kwargs)

        return HttpResponseForbidden()

    def get(self, request, *args, **kwargs):
        json_data = kwargs.get('route').as_dict()
        return self.prepare_response(request, json_data=json_data, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # save post
        return self.prepare_response(request, json_data={'status': 'OK'}, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        # save post
        return self.prepare_response(request, json_data={'status': 'OK'}, *args, **kwargs)


class RouteLocationView(LoginRequiredMixin, JsonView):
    http_method_names = ['post', 'delete']


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

from django.views.generic import View, TemplateView

from lr2_api.base_views import JsonView, PaginateMixin
from lr2_api.models import Location, TravelCompany


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


class PersonalInfoView(JsonView):
    http_method_names = ['get']

    def get_json_data(self, user, **kwargs):
        return user.as_dict()


class MyRoutesView(PaginateMixin, JsonView):
    http_method_names = ['get']
    data_key = 'routes'

    def get_queryset(self, user, **kwargs):
        return user.route_set.all()


class RouteView(JsonView):
    http_method_names = ['get', 'post', 'patch']


class RouteLocationView(JsonView):
    http_method_names = ['post', 'delete']


class RouteRegisterView(JsonView):
    http_method_names = ['post']

from django.conf.urls import url

from lr2_api.views import LocationsView, TravelCompaniesView, \
    PersonalInfoView, MyRoutesView, RouteView, RouteLocationView, RouteRegisterView, AuthorizeView, AccessTokenView

urlpatterns = [
    # auth
    url(r'^authorize/$',
        AuthorizeView.as_view(),
        name='authorize'),

    url(r'^access_token/$',
        AccessTokenView.as_view(),
        name='access_token'),

    # public
    url(r'^locations/$',
        LocationsView.as_view(),
        name='locations'),

    url(r'^companies/$',
        TravelCompaniesView.as_view(),
        name='travel_companies'),

    # by token
    url(r'^me/$',
        PersonalInfoView.as_view(),
        name='me'),

    url(r'^routes/$',
        MyRoutesView.as_view(),
        name='my_routes'),

    url(r'^route/(?P<route_id>\d+)/$',
        RouteView.as_view(),
        name='route'),

    url(r'^route/(?P<route_id>\d+)/location/(?P<location_id>\d+)/$',
        RouteLocationView.as_view(),
        name='route_location'),

    url(r'^route/(?P<route_id>\d+)/register/',
        RouteRegisterView.as_view(),
        name='register')
]

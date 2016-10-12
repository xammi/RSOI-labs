from django.conf.urls import url
from lr1_oauth.views import IndexView, SuccessView, get_tweet, ErrorView, manual_start, manual_complete

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^success/', SuccessView.as_view(), name='success'),
    url(r'^error/', ErrorView.as_view(), name='error'),
    url(r'^get_tweet/(?P<backend>[^/]+)/$', get_tweet, name='get_tweet'),

    url(r'^manual/', manual_start, name='manual'),
    url(r'^complete/', manual_complete, name='complete')
]

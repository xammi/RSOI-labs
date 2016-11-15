from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^social/', include('social.apps.django_app.urls', namespace='social')),

    url(r'^oauth/', include('lr1_oauth.urls', namespace='oauth')),
    url(r'^api/', include('lr2_api.urls', namespace='api')),
]

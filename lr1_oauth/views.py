import string
import requests
from urllib.parse import urlencode

from django.utils.crypto import get_random_string
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseBadRequest
from django.views.generic import TemplateView
from django.conf import settings
from django.contrib.auth import login

from social.apps.django_app.default.models import UserSocialAuth
from social.utils import setting_name
from social.apps.django_app.utils import psa

from lr1_oauth.utils import parse_qs, OAuth1

NAMESPACE = getattr(settings, setting_name('URL_NAMESPACE'), None) or 'social'


class IndexView(TemplateView):
    http_method_names = ['get']
    template_name = 'lr1_oauth/index.html'


class SuccessView(TemplateView):
    http_method_names = ['get']
    template_name = 'lr1_oauth/success.html'


class ErrorView(TemplateView):
    http_method_names = ['get']
    template_name = 'lr1_oauth/error.html'

    errors = {
        'denied': 'пользователь не хочет давать права',
        'user_refused': 'твиттер не подтвердил пользователя',
        'user_not_active': 'пользователь не активен'
    }
    def_error = 'неизвестная ошибка'

    def get_context_data(self, **kwargs):
        context = super(ErrorView, self).get_context_data(**kwargs)
        oauth_error = self.request.session.pop('oauth_error')
        context['err_msg'] = self.errors.get(oauth_error, self.def_error)
        return context


@psa('{0}:complete'.format(NAMESPACE))
def get_tweet(request, backend):
    backend = request.backend
    social = UserSocialAuth.objects.filter(user_id=request.user.id).first()
    if social:
        tweet = backend.get_json(
            'https://api.twitter.com/1.1/statuses/show.json',
            params={'id': '784737275766681600'},
            auth=backend.oauth_auth(social.access_token)
        )
    return JsonResponse(tweet)


def manual_start(request):
    key = settings.SOCIAL_AUTH_TWITTER_KEY
    secret = settings.SOCIAL_AUTH_TWITTER_SECRET
    state = get_random_string(32, string.ascii_letters + string.digits)
    request.session['state'] = state

    req_token_url = 'https://api.twitter.com/oauth/request_token'
    req_token_method = 'POST'
    redirect_uri = 'http://rsoi.local/oauth/complete/?redirect_state={}'.format(state)
    auth = OAuth1(key, secret, callback_uri=redirect_uri, decoding=None)

    response = requests.request(req_token_method, req_token_url, headers={}, params={}, auth=auth, timeout=None)
    response.raise_for_status()
    content = response.content

    token = content.decode(response.encoding)
    request.session['token'] = token
    token_data = parse_qs(token)

    print('\nПервый запрос\n', token_data)

    params = {
        'oauth_token': token_data.get('oauth_token'),
        'redirect_uri': redirect_uri
    }
    auth_url = 'https://api.twitter.com/oauth/authenticate'
    auth_url = '{0}?{1}'.format(auth_url, urlencode(params))
    return HttpResponseRedirect(redirect_to=auth_url)


def manual_complete(request):
    data = request.GET

    print('\nПосле редиректа\n', data)

    if 'denied' in data:
        request.session['oauth_error'] = 'denied'
        return HttpResponseRedirect('/oauth/error/')

    if 'oauth_problem' in data:
        request.session['oauth_error'] = data['oauth_problem']
        return HttpResponseRedirect('/oauth/error/')

    state = request.session.get('state')
    token = request.session.get('token')
    if not state or not token:
        return HttpResponseNotFound()

    req_state = data.get('redirect_state')
    req_token = data.get('oauth_token')
    if not req_state or not state == req_state:
        return HttpResponseBadRequest()

    token_data = parse_qs(token)
    if not token_data.get('oauth_token') == req_token:
        return HttpResponseBadRequest()

    key = settings.SOCIAL_AUTH_TWITTER_KEY
    secret = settings.SOCIAL_AUTH_TWITTER_SECRET
    oauth_verifier = data.get('oauth_verifier')

    resource_owner_key = token_data.get('oauth_token')
    resource_owner_secret = token_data.get('oauth_token_secret')
    if not resource_owner_key or not resource_owner_secret:
        return HttpResponseNotFound()

    redirect_uri = 'http://rsoi.local/oauth/complete/?redirect_state={}'.format(state)
    auth = OAuth1(key, secret, resource_owner_key=resource_owner_key, resource_owner_secret=resource_owner_secret,
                  callback_uri=redirect_uri, verifier=oauth_verifier, decoding=None)

    access_method = 'POST'
    access_url = 'https://api.twitter.com/oauth/access_token'
    response = requests.request(access_method, access_url, auth=auth)
    response.raise_for_status()
    access_token = parse_qs(response.text)

    print('\nAccess token\n', access_token)

    resource_owner_key = access_token.get('oauth_token')
    resource_owner_secret = access_token.get('oauth_token_secret')
    if not resource_owner_key or not resource_owner_secret:
        return HttpResponseNotFound()

    user_method = 'GET'
    user_url = 'https://api.twitter.com/1.1/account/verify_credentials.json'
    params = {'include_email': 'true'}
    auth = OAuth1(key, secret, resource_owner_key=resource_owner_key, resource_owner_secret=resource_owner_secret,
                  callback_uri=redirect_uri, decoding=None)

    response = requests.request(user_method, user_url, params=params, auth=auth)
    response.raise_for_status()

    data = response.json()
    if data and 'access_token' not in data:
        data['access_token'] = access_token

    print('\nДанные пользователя\n', data)

    user = request.user
    is_authenticated = user.is_authenticated()
    if is_authenticated:
        return HttpResponseRedirect(redirect_to='/oauth/success/')

    user_social = UserSocialAuth.objects.filter(uid=data.get('id')).first()
    if user_social:
        user = user_social.user
    else:
        request.session['oauth_error'] = 'user_not_active'
        return HttpResponseRedirect(redirect_to='/oauth/error/')

    if user.is_active:
        user.__dict__['backend'] = 'social.backends.twitter.TwitterOAuth'
        login(request, user)
        return HttpResponseRedirect(redirect_to='/oauth/success/')
    else:
        request.session['oauth_error'] = 'user_not_active'
        return HttpResponseRedirect(redirect_to='/oauth/error/')


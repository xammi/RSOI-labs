import hmac
import time
import random

from hashlib import sha1
from binascii import b2a_base64
from urllib.parse import quote, urlparse, urlunparse, parse_qsl
from requests.utils import to_native_string
from requests.auth import AuthBase


class OAuth1(AuthBase):
    default_ports = {
        'http': '80',
        'https': '443'
    }

    def __init__(self, client_key, client_secret, resource_owner_key=None, resource_owner_secret=None,
                 callback_uri=None, verifier=None):

        self.client = {'key': client_key or '', 'secret': client_secret or ''}
        self.resource_owner = {'key': resource_owner_key or '', 'secret': resource_owner_secret or ''}
        self.callback_uri = callback_uri
        self.verifier = verifier

    def __call__(self, r):
        r.url, headers, _ = self.sign(r)
        r.prepare_headers(headers)
        r.url = to_native_string(r.url)
        return r

    def sign(self, request):
        timestamp = str(int(time.time()))
        nonce = str(random.getrandbits(64)) + timestamp
        timestamp = str(int(time.time()))
        params = [
            ('oauth_nonce', nonce),
            ('oauth_timestamp', timestamp),
            ('oauth_version', '1.0'),
            ('oauth_signature_method', 'HMAC-SHA1'),
            ('oauth_consumer_key', self.client['key']),
        ]
        if self.resource_owner['key']:
            params.append(('oauth_token', self.resource_owner['key']))
        if self.callback_uri:
            params.append(('oauth_callback', self.callback_uri))
        if self.verifier:
            params.append(('oauth_verifier', self.verifier))

        request.oauth_params = params
        signature = self.get_oauth_signature(request)
        request.oauth_params.append(('oauth_signature', signature))
        return self._render(request)

    def get_oauth_signature(self, request):
        url, headers, body = self._render(request)
        scheme, netloc, path, params, query, fragment = urlparse(url)

        collected_params = request.oauth_params + parse_qsl(query, keep_blank_values=True)
        key_values = [(escape(k), escape(v)) for k, v in collected_params]
        parameter_parts = ['{0}={1}'.format(k, v) for k, v in sorted(key_values)]
        normalized_params = '&'.join(parameter_parts)

        path = path or '/'
        host = headers.get('Host', None)
        scheme, netloc = scheme.lower(), netloc.lower()
        if host is not None:
            netloc = host.lower()

        if ':' in netloc:
            host, port = netloc.split(':', 1)
            if (scheme, port) in self.default_ports.items():
                netloc = host

        normalized_uri = urlunparse((scheme, netloc, path, params, '', ''))

        base_string = escape(request.method.upper()) + '&' + \
                      escape(normalized_uri) + '&' + \
                      escape(normalized_params)

        key = escape(self.client['secret']) + '&' + \
              escape(self.resource_owner['secret'])

        signature = hmac.new(key.encode('utf-8'), base_string.encode('utf-8'), sha1).digest()
        return b2a_base64(signature)[:-1].decode('utf-8')

    @staticmethod
    def _render(request):
        url, headers, body = request.url, request.headers, request.body

        auth_header_parts = []
        for name, value in request.oauth_params:
            part = '{0}="{1}"'.format(escape(name), escape(value))
            auth_header_parts.append(part)

        auth_header = 'OAuth {0}'.format(', '.join(auth_header_parts))
        headers['Authorization'] = auth_header
        return url, headers, body


def parse_qs(token):
    token_data = {}
    for pair in token.split('&'):
        key, value = pair.split('=')
        token_data[key] = value
    return token_data


def escape(string):
    return quote(string.encode('utf-8'), b'~')

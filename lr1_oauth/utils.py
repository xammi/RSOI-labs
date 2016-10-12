from oauthlib.oauth1 import Client
from requests.utils import to_native_string
from requests.auth import AuthBase


class OAuth1(AuthBase):
    def __init__(self, client_key, client_secret, resource_owner_key=None, resource_owner_secret=None,
                 callback_uri=None, verifier=None):

        self.client = Client(client_key, client_secret, resource_owner_key, resource_owner_secret,
                             callback_uri, verifier=verifier)

    def __call__(self, r):
        r.url, headers, _ = self.client.sign(str(r.url), str(r.method), None, r.headers)
        r.prepare_headers(headers)
        r.url = to_native_string(r.url)
        return r

    def sign(self, uri, http_method, body=None, headers=None):
        pass


def parse_qs(token):
    token_data = {}
    for pair in token.split('&'):
        key, value = pair.split('=')
        token_data[key] = value
    return token_data

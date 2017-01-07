import base64
import random

import binascii
from urllib.parse import unquote_plus

from flask import jsonify, make_response
from datetime import datetime


class Error(Exception):
    def __init__(self, code, *args, **kwargs):
        super(Error, self).__init__(*args, **kwargs)
        self.code = code


def current_time():
    return datetime.now().strftime('%d-%m-%y %H:%M:%S')


def send_error(request, code):
    return '', code


class Logger:
    @staticmethod
    def error(request, code):
        print('ERROR [%s] %s %s %s'.format(current_time(), request.method, request.url, code))

    @staticmethod
    def success(request):
        print('SUCCESS [%s] %s %s %s'.format(current_time(), request.method, request.url, 200))


def remove_object_ids(data):
    if isinstance(data, dict):
        if '_id' in data:
            data['_id'] = str(data['_id'])

        for value in data.values():
            remove_object_ids(value)

    if isinstance(data, list):
        for item in data:
            remove_object_ids(item)


def send_response(request, response):
    remove_object_ids(response)
    json = jsonify(response)
    response = make_response(json)
    response.headers['Content-Type'] = "application/json"
    return response


def convert_or_400(value, type):
    try:
        return type(value)
    except (ValueError, TypeError) as e:
        raise Error(400, str(e))


def cursor_to_list(cursor):
    return [item for item in cursor]


def generate_token(length=30, chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    rand = random.SystemRandom()
    return ''.join(rand.choice(chars) for _ in range(length))


def extract_client(request, apps):
    try:
        enc = request.charset or 'utf-8'
    except AttributeError:
        enc = 'utf-8'
    auth_string = request.headers.environ.get('HTTP_AUTHORIZATION')
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

    app = apps.get(client_id)
    if app and app['client_secret'] == client_secret:
        return app
    return None


def check_access(request, access_collection):
    auth_header = request.headers.environ.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer'):
        return None

    token = auth_header[7:]
    grant = access_collection.find({'access_token': token, 'expires_in': {'$gt': datetime.now()}})
    if grant.count() == 0:
        return None

    grant = cursor_to_list(grant)[0]
    return grant['user']

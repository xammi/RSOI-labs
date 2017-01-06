import random
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

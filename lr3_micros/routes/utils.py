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


def paginate(request, data):
    size = convert_or_400(request.args.get('size', 10), int)
    page = convert_or_400(request.args.get('page', 1), int)

    result = {'size': size, 'page': page, 'data': []}
    if size <= 0:
        return result

    if page <= 0 or page > (data.count() // size) + 1:
        raise Error(404)

    data = data[(page-1)*size: page*size]
    result['data'] = cursor_to_list(data)
    return result

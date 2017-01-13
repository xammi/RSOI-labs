from flask import jsonify, make_response


def send_error(request, code):
    return '', code


def send_response(request, response):
    json = jsonify(response)
    response = make_response(json)
    response.headers['Content-Type'] = "application/json"
    return response


def clean_hh(request):
    headers = {}
    for name in ['HTTP_AUTHORIZATION']:
        if name in request.headers.environ:
            headers[name] = request.headers.environ.get(name)
    return headers

from flask import jsonify, make_response
import requests
from requests.exceptions import ConnectionError


def send_error(request, code):
    return '', code


def send_response(request, response_data):
    json = jsonify(response_data)
    response = make_response(json)
    response.headers['Content-Type'] = "application/json"
    return response


def clean_hh(request):
    headers = {}
    for name in ['HTTP_AUTHORIZATION']:
        if name in request.headers.environ:
            fitted_name = name.split('_')[1]
            headers[fitted_name] = request.headers.environ.get(name)
    return headers


def proxy_to(request, url):
    try:
        response = requests.request(request.method, url, data=request.form, params=request.args,
                                    headers=clean_hh(request), cookies=request.cookies)
        return response.content, response.status_code
    except ConnectionError:
        return send_response(request, {'status': 'Session service is down'})

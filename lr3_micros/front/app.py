import json
import requests
from requests.exceptions import ConnectionError
from flask import Flask, request, redirect
from lr3_micros.front.utils import send_error, send_response, clean_hh, proxy_to


app = Flask(__name__)


COMPANY_SERVICE_URL = 'http://127.0.0.1:9092/'
ROUTE_SERVICE_URL = 'http://127.0.0.1:9093/'
SESSIONS_SERVICE_URL = 'http://127.0.0.1:9091/'


@app.route('/login/', methods=['GET', 'POST'])
def login_proxy():
    return proxy_to(request, SESSIONS_SERVICE_URL + 'login/')


@app.route('/register/', methods=['GET', 'POST'])
def register_proxy():
    return proxy_to(request, SESSIONS_SERVICE_URL + 'register/')


@app.route('/authorize/', methods=['GET', 'POST'])
def authorize_proxy():
    return proxy_to(request, SESSIONS_SERVICE_URL + 'authorize/')


@app.route('/token/', methods=['POST'])
def access_token_proxy():
    return proxy_to(request, SESSIONS_SERVICE_URL + 'token/')


@app.route('/me/', methods=['GET'])
def personal_view():
    try:
        response = requests.get(SESSIONS_SERVICE_URL + 'identify/', headers=clean_hh(request))
        if response.status_code != 200:
            return send_error(request, 403)
    except ConnectionError as e:
        return send_response(request, {'status': 'Session service is down'})

    user = response.json()['data']
    headers = {'X_EMAIL': user['email']}
    try:
        response = requests.get(COMPANY_SERVICE_URL + 'companies/', headers=headers)
        if response.status_code == 200:
            companies = json.loads(response.text)
            user['companies'] = companies['data']
    except ConnectionError as e:
        user['companies'] = {'error': 'Company service is down'}

    try:
        response = requests.get(ROUTE_SERVICE_URL + 'my_routes/', headers=headers)
        if response.status_code == 200:
            routes = json.loads(response.text)
            user['routes'] = routes['data']
    except ConnectionError as e:
        user['routes'] = {'error': 'Routes service is down'}

    return send_response(request, {'status': 'OK', 'data': user})


@app.route('/route/<route_id>/register/', methods=['POST'])
def register_me(route_id):
    try:
        response = requests.get(SESSIONS_SERVICE_URL + 'identify/', headers=clean_hh(request))
        if response.status_code != 200:
            return send_error(request, 403)
    except ConnectionError:
        return send_response(request, {'status': 'Session service is down'})

    user = response.json()['data']
    headers = {'X_EMAIL': user['email']}
    try:
        response = requests.post(ROUTE_SERVICE_URL + 'route/%s/register/' % route_id, headers=headers)
        if response.status_code == 200:
            return send_response(request, {'status': 'OK'})
        return send_error(request, response.status_code)
    except ConnectionError:
        return send_response(request, {'status': 'Route service is down'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9094)

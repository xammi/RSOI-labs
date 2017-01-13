import requests
import json
from flask import Flask, request, redirect
from lr3_micros.front.utils import send_error, send_response, clean_hh


app = Flask(__name__)


COMPANY_SERVICE_URL = 'http://127.0.0.1:9092/'
ROUTE_SERVICE_URL = 'http://127.0.0.1:9093/'
SESSIONS_SERVICE_URL = 'http://127.0.0.1:9091/'


@app.route('/login/', methods=['GET', 'POST'])
def login_proxy():
    url = SESSIONS_SERVICE_URL + 'login/'
    response = requests.request(request.method, url, params=request.values, headers=clean_hh(request))
    return response.content, response.status_code


@app.route('/register/', methods=['GET', 'POST'])
def register_proxy():
    url = SESSIONS_SERVICE_URL + 'register/'
    response = requests.request(request.method, url, params=request.values, headers=clean_hh(request))
    return response.content, response.status_code


@app.route('/authorize/', methods=['GET', 'POST'])
def authorize_proxy():
    url = SESSIONS_SERVICE_URL + 'authorize/'
    response = requests.request(request.method, url, params=request.values, headers=clean_hh(request))
    return response.content, response.status_code


@app.route('/token/', methods=['POST'])
def access_token_proxy():
    url = SESSIONS_SERVICE_URL + 'token/'
    response = requests.post(url, params=request.values, headers=clean_hh(request))
    return response.content, response.status_code


@app.route('/me/', methods=['GET'])
def personal_view():
    response = requests.get(SESSIONS_SERVICE_URL + 'identify/', headers=clean_hh(request))
    if response.status_code != 200:
        return send_error(request, 403)

    user = response.json()
    headers = {'X_EMAIL': user['email']}
    response = requests.get(COMPANY_SERVICE_URL + 'companies/', headers=headers)
    if response.status_code == 200:
        companies = json.loads(response.text)
        user['companies'] = companies['data']

    response = requests.get(ROUTE_SERVICE_URL + 'my_routes/', headers=headers)
    if response.status_code == 200:
        routes = json.loads(response.text)
        user['routes'] = routes['data']

    return send_response(request, {'status': 'OK', 'data': user})


@app.route('/route/<route_id>/register/', methods=['POST'])
def register_me(route_id):
    response = requests.get(SESSIONS_SERVICE_URL + 'identify/', headers=clean_hh(request))
    if response.status_code != 200:
        return send_error(request, 403)

    user = response.json()
    headers = {'X_EMAIL': user}
    response = requests.post(ROUTE_SERVICE_URL + 'route/%s/register/' % route_id, headers=headers)
    if response.status_code == 200:
        return send_response(request, {'status': 'OK'})
    return send_error(request, response.status_code)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9094)

import json
import requests
from flask import Flask, request

app = Flask(__name__)

user_data = {
    'email': 'kmg.xammi.1@gmail.com',
    'first_name': 'Maksim',
    'last_name': 'Kislenko',
}
server_data = {
    'host': '127.0.0.1',
    'port': '9011',
    'api_key': '1435',
    'api_secret': 'BiuyiuwqIYBI3123',
}
client_data = {
    'host': '127.0.0.1',
    'port': '9012',
}


def get_server_route(route):
    return 'http://{0}:{1}/{2}'.format(server_data['host'], server_data['port'], route)


@app.route('/redirect/')
def finish_auth():
    code = request.args.get('code')
    data = {'grant_type': 'authorization_code', 'code': code}
    finish_url = get_server_route('api/access_token')
    auth_data = (server_data['api_key'], server_data['api_secret'])

    r = requests.post(finish_url, data=data, auth=auth_data)
    if r.status_code == 200:
        token = r.json()["access_token"]
        print(token)


def start_auth():
    start_url = get_server_route('api/authorize')
    start_params = {
        'client_id': server_data['api_key'],
        'response_type': 'code',
    }
    response = requests.get(start_url, params=start_params)
    print('Started: ', response.status_code)


if __name__ == '__main__':
    app.run(host=client_data['host'], port=client_data['port'])
    start_auth()


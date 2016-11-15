import requests
from flask import Flask, request, redirect, make_response

app = Flask(__name__)

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


@app.route('/redirect/', methods=['GET'])
def finish_auth():
    code = request.args.get('code')
    if not code:
        return make_response(400)

    data = {'grant_type': 'authorization_code', 'code': code}
    finish_url = get_server_route('api/access_token')
    auth_data = (server_data['api_key'], server_data['api_secret'])

    response = requests.post(finish_url, data=data, auth=auth_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(token)


@app.route('/start_auth/', methods=['GET'])
def start_auth():
    start_url = get_server_route('api/authorize')
    start_params = {
        'client_id': server_data['api_key'],
        'response_type': 'code',
    }
    params = '?'
    for param, value in start_params.items():
        params += '{0}={1}&'.format(param, value)
    return redirect(start_url + params[:-1])


index_template = '''
<html>
<head><title>LR2 Client</title></head>
<body><a href="/start_auth/">Авторизоваться</a></body>
</html>
'''


@app.route('/', methods=['GET'])
def index():
    return index_template


if __name__ == '__main__':
    app.run(host=client_data['host'], port=client_data['port'])


import requests
from flask import Flask, request, redirect, make_response, jsonify

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


def send_response(status, obj=None):
    json = jsonify({'code': status, 'response': obj})
    response = make_response(json)
    response.headers['Content-Type'] = "application/json"
    return response


query_template = '''
<html>
<head><title>LR2 Client</title></head><body>
<h3>Сделать запрос в API</h3><div id="query-form">
<form action="/query/" method="POST"><input type="text" name="query"><button type="submit">Send</button></form>
</div><div id="query-data">{0}</div></body>
</html>
'''


@app.route('/query/', methods=['GET', 'POST'])
def send_query():
    if request.method == 'POST':
        query = request.args.post('query')
        token = client_data.get('access_token')
        if not token:
            return send_response('ERROR', {'msg': 'No token', 'query': query})
        url = get_server_route(query)
        response = requests.request('GET', url, headers={'Authorization': 'Bearer:{0}'.format(token)})
        if response.status_code != 200:
            return send_response('ERROR', '{} code for {}'.format(response.status_code, url))
        result = response.json()
    else:
        result = ''
    return query_template.format(result)


@app.route('/redirect/', methods=['GET'])
def finish_auth():
    code = request.args.get('code')
    if not code:
        return send_response('ERROR')

    data = {'grant_type': 'authorization_code', 'code': code}
    finish_url = get_server_route('api/access_token/')
    auth_data = (server_data['api_key'], server_data['api_secret'])

    response = requests.post(finish_url, data=data, auth=auth_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        client_data['access_token'] = token
        return redirect('/query/')
    return send_response('ERROR', 'Not 200 on api/access_token/')


@app.route('/start_auth/', methods=['GET'])
def start_auth():
    start_url = get_server_route('api/authorize/')
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


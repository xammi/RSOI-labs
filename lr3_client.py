from datetime import datetime, timedelta
import requests
from flask import Flask, request, redirect, make_response, jsonify
import json

app = Flask(__name__)

#TODO: make map of URLs to servers
server_data = {
    'host': '127.0.0.1',
    'port': '9091',
    'api_key': 'EftqgfZ8YCxmUSa7tLIm9NZYW3X0hLhzktyUlwHV',
    'api_secret': 'It9aTzpJP9bzS1KLCEyPi8xBsB1WPxHpMxbArCec7tT7ifky5RodBHeiOzJ9lMEv8tkb9Fzs4Zc1zLY5Uqj43OQKVWq15QmN5dPtHxl2wEmlL0ZKPJppAElyfs6cO9Jm',
}
client_data = {
    'host': '127.0.0.1',
    'port': '9090',
}
AUTHORIZE_URL = 'authorize'
ACCESS_TOKEN_URL = 'token'


def get_server_route(route):
    backslash = '?' not in route
    return 'http://{0}:{1}/{2}'.format(
        server_data['host'], server_data['port'], route) + ('/' if backslash else '')


def get_client_route(route):
    backslash = '?' not in route
    return 'http://{0}:{1}/{2}'.format(client_data['host'], client_data['port'], route) + ('/' if backslash else '')


def send_response(status, obj=None):
    json = jsonify({'code': status, 'response': obj})
    response = make_response(json)
    response.headers['Content-Type'] = "application/json"
    return response


query_template = '''
<html>
<head><title>LR2 Client</title><meta charset="utf-8"></head>
<body>
  <div>Access Token: {1}</div>
  <h3>Сделать запрос в API</h3><div id="query-form">

  <form action="/query/" method="POST">
    <select name="method">
      <option value="GET">GET</option>
      <option value="POST">POST</option>
      <option value="PATCH">PATCH</option>
      <option value="DELETE">DELETE</option>
    </select>
    <input type="text" name="query" style="width:400px" value="{2}"><br><br>
    <textarea name="body">{3}</textarea><br><br>
    <button type="submit">Send</button>
  </form>

  </div><pre id="query-data">{0}</pre>
</body>
</html>
'''


@app.route('/query/', methods=['GET', 'POST'])
def send_query():
    token = client_data.get('access_token')
    if not token:
        return send_response('ERROR', {'msg': 'No token'})

    if request.method == 'POST':
        query = request.form.get('query')
        method = request.form.get('method')
        body = request.form.get('body')
        url = get_server_route(query)
        headers = {'Authorization': 'Bearer:{0}'.format(token)}
        if not body:
            response = requests.request(method, url, headers=headers)
        else:
            data = json.loads(body.replace(r'\n\r', '').replace(',}', '}'))
            response = requests.request(method, url, headers=headers, data=data)

        if response.status_code != 200:
            result = 'ERROR', '{} code for {}'.format(response.status_code, url)
        else:
            result = json.dumps(response.json(), indent=4, ensure_ascii=False)
        return query_template.format(result, client_data.get('access_token'), query, body or '')
    return query_template.format('', client_data.get('access_token'), '', '')


@app.route('/redirect/', methods=['GET'])
def finish_auth():
    code = request.args.get('code')
    if not code:
        return send_response('ERROR')

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': get_client_route('redirect'),
    }
    finish_url = get_server_route(ACCESS_TOKEN_URL)
    auth_data = (server_data['api_key'], server_data['api_secret'])

    response = requests.post(finish_url, data=data, auth=auth_data)
    if response.status_code == 200:
        resp_data = response.json()
        client_data.update({
            'access_token': resp_data.get('access_token'),
            'refresh_token': resp_data.get('refresh_token'),
            'expires_in': datetime.now() + timedelta(seconds=resp_data.get('expires_in')),
        })

        return redirect('/query/')
    return send_response('ERROR', 'Not 200')


@app.route('/start_auth/', methods=['GET'])
def start_auth():
    start_url = get_server_route(AUTHORIZE_URL)
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


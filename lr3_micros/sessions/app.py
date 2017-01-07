import requests
import json
from hashlib import sha256 as get_hash
from flask import Flask, request, redirect, session
from flask.ext.pymongo import PyMongo
from lr3_micros.sessions.utils import send_response, send_error, cursor_to_list, generate_token, extract_client, \
    check_access
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote, urlparse, unquote


app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'sessions_bd'
app.secret_key = 'euh45wiufhewiyyIOYE2345IUWIFUYEWew2345yfu'
app.config['SESSION_TYPE'] = 'mongodb'
mongo = PyMongo(app)

USER_FIELDS = ['email', 'password', 'first_name', 'last_name']
SECRET_HEADER = 'ewifyw521763eyuwfgeuwYTWDYA'


base_tmpl = '''
<html>
  <head><title>LR3 Client</title><meta charset="utf-8"></head>
  <body>%(content)s</body>
</html>
'''

register_tmpl = base_tmpl % {'content': '''
<form action="/register/" method="post">
  <label for="id_email">Email:</label><input name="email" id="id_email" type="email"/>
  <label for="id_password">Пароль:</label><input name="password" id="id_password" type="password"/>
  <label for="id_first_name">Имя:</label><input name="first_name" id="id_first_name" type="text"/>
  <label for="id_last_name">Фамилия:</label><input name="last_name" id="id_last_name" type="text"/>
  <button type="submit">Отправить</button>
</form>
<a href="/login/">Авторизация</a>
'''}

auth_tmpl = base_tmpl % {'content': '''
<div id="content">
  <h3>Вы уже авторизованы как:</h3>
  <h3>%s</h3>
</div>
<a href="/logout/">Выйти</a>
'''}


@app.route('/register/', methods=['GET', 'POST'])
def register_view():
    if request.method == 'GET':
        auth = session.get('email')
        return auth_tmpl % auth if auth else register_tmpl

    elif request.method == 'POST':
        user = {field: request.form.get(field) for field in USER_FIELDS}
        if not user['email'] or not user['password']:
            return send_error(request, 400)

        yet_created = mongo.db.user.find({'email': user['email']}).count()
        if yet_created > 0:
            return send_error(request, 400)

        user['password'] = get_hash(user['password'].encode('ascii')).hexdigest()
        user['created'] = datetime.now()
        mongo.db.user.insert(user)
        return redirect('/login/')


login_tmpl = base_tmpl % {'content': '''
<form action="%s" method="post">
  <label for="id_email">Email:</label><input name="email" id="id_email" type="email"/>
  <label for="id_password">Пароль:</label><input name="password" id="id_password" type="password"/>
  <button type="submit">Отправить</button>
</form>
<a href="/register/">Регистрация</a>
'''}


@app.route('/login/', methods=['GET', 'POST'])
def login_view():
    if request.method == 'GET':
        auth = session.get('email')
        return auth_tmpl % auth if auth else login_tmpl % request.url

    elif request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            return send_error(request, 400)

        password = get_hash(password.encode('ascii')).hexdigest()
        users_cursor = mongo.db.user.find({'email': email, 'password': password})
        if users_cursor.count() == 0:
            return send_error(request, 404)

        user = cursor_to_list(users_cursor)[0]
        session['email'] = user['email']

        if 'next' in request.args:
            redirect_uri = unquote(request.args.get('next'))
            return redirect(redirect_uri)
        return send_response(request, {'status': 'Authorized'})


@app.route('/logout/', methods=['GET'])
def logout_view():
    session.pop('email', None)
    return redirect('/login/')


allow_tmpl = base_tmpl % {'content': '''
<h3>Вы доверяете клиентскому приложению?</h3>
<form action="/authorize/" method="post">
  <p>Выполнение API запросов</p>
  <input type="radio" name="allow"/>
  <input type="hidden" name="redirect_uri" value="%(redirect_uri)s"/>
  <input type="hidden" name="client_id" value="%(client_id)s"/>
  <input type="hidden" name="response_type" value="%(response_type)s"/>
  <button type="submit">Отправить</button>
</form>
'''}


OAUTH2_APPS = {
    'EftqgfZ8YCxmUSa7tLIm9NZYW3X0hLhzktyUlwHV': {
        'client_id': 'EftqgfZ8YCxmUSa7tLIm9NZYW3X0hLhzktyUlwHV',
        'client_secret': 'It9aTzpJP9bzS1KLCEyPi8xBsB1WPxHpMxbArCec7tT7ifky5RodBHeiOzJ9lMEv8tkb9Fzs4Zc1zLY5Uqj43OQKVWq15QmN5dPtHxl2wEmlL0ZKPJppAElyfs6cO9Jm',
        'callback_uri': 'http://127.0.0.1:9090/redirect/',
    },
}


@app.route('/authorize/', methods=['GET', 'POST'])
def authorize_view():
    if request.method == 'GET':
        auth = session.get('email')
        if not auth:
            redirect_uri = '/login/?next=%s' % quote(request.url)
            return redirect(redirect_uri)

        client_id = request.args.get('client_id')
        response_type = request.args.get('response_type')
        if not client_id or response_type.lower() != 'code':
            return send_error(request, 400)

        codes = mongo.db.OAuth2Code.find({'client_id': client_id, 'user': auth, 'expires': {'$gt': datetime.now()}})
        if codes.count() > 0:
            token = generate_token()
            expires = datetime.now() + timedelta(seconds=60)
            mongo.db.OAuth2Code.update_one({'client_id': client_id, 'user': auth}, {'token': token, 'expires': expires})
            redirect_uri = request.form.get('redirect_uri') + '?code=%s' % token
            return redirect(redirect_uri)

        form_values = {
            'client_id': client_id, 'response_type': response_type,
            'redirect_uri': OAUTH2_APPS.get(client_id, {}).get('callback_uri'),
        }
        return allow_tmpl % form_values

    elif request.method == 'POST':
        allow = request.form.get('allow')
        if not allow:
            return redirect('/login/')

        token = {
            'token': generate_token(),
            'expires': datetime.now() + timedelta(seconds=60),
            'user': session.get('email'),
            'app': request.form.get('client_id'),
        }
        mongo.db.OAuth2Code.insert(token)
        redirect_uri = request.form.get('redirect_uri') + '?code=%s' % token['token']
        return redirect(redirect_uri)


@app.route('/token/', methods=['POST'])
def access_token_view():
    grant_type = request.form.get('grant_type')
    code = request.form.get('code')
    if grant_type.lower() != 'authorization_code' or not code:
        return send_error(request, 400)

    app = extract_client(request, OAUTH2_APPS)
    grant = mongo.db.OAuth2Code.find({'app': app['client_id'], 'token': code, 'expires': {'$gt': datetime.now()}})
    if grant.count() == 0:
        return send_error(request, 404)

    grant = cursor_to_list(grant)[0]
    token = {
        'expires_in': datetime.now() + timedelta(seconds=36000),
        'access_token': generate_token(),
        'refresh_token': generate_token(),
        'token_type': 'Bearer',
        'user': grant['user'],
    }
    mongo.db.OAuth2Access.insert(token)
    mongo.db.OAuth2Code.delete_one({'token': code, 'app': app['client_id']})
    token['expires_in'] = 36000
    return send_response(request, token)


COMPANY_SERVICE_URL = 'http://127.0.0.1:9092/'
ROUTE_SERVICE_URL = 'http://127.0.0.1:9093/'


@app.route('/me/', methods=['GET'])
def personal_view():
    user = check_access(request, mongo.db.OAuth2Access)
    if not user:
        return send_error(request, 403)

    user_data = mongo.db.user.find({'email': user})
    user_data = cursor_to_list(user_data)[0]
    del user_data['password']
    if request.args.get('internal'):
        return send_response(request, {'status': 'OK', 'data': user_data})

    headers = {'X_EMAIL': user_data['email'], 'X_SECRET': SECRET_HEADER}
    response = requests.get(COMPANY_SERVICE_URL + 'companies/', headers=headers)
    if response.status_code == 200:
        companies = json.loads(response.text)
        user_data['companies'] = companies['data']

    response = requests.get(ROUTE_SERVICE_URL + 'my_routes/', headers=headers)
    if response.status_code == 200:
        routes = json.loads(response.text)
        user_data['routes'] = routes['data']

    return send_response(request, {'status': 'OK', 'data': user_data})


@app.route('/route/<route_id>/register/', methods=['POST'])
def register_me(route_id):
    user = check_access(request, mongo.db.OAuth2Access)
    if not user:
        return send_error(request, 403)

    headers = {'X_EMAIL': user, 'X_SECRET': SECRET_HEADER}
    response = requests.post(ROUTE_SERVICE_URL + 'route/%s/register/' % route_id, headers=headers)
    if response.status_code == 200:
        return send_response(request, {'status': 'OK'})
    return send_error(request, response.status_code)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9091)

from hashlib import sha256 as get_hash
from flask import Flask, request, redirect, session, render_template
from flask.ext.pymongo import PyMongo
from lr3_micros.sessions.utils import send_response, send_error, cursor_to_list, generate_token, extract_client
from datetime import datetime, timedelta
from urllib.parse import quote, unquote


app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'sessions_bd'
app.secret_key = 'euh45wiufhewiyyIOYE2345IUWIFUYEWew2345yfu'
app.config['SESSION_TYPE'] = 'mongodb'
mongo = PyMongo(app)

USER_FIELDS = ['email', 'password', 'first_name', 'last_name']


@app.route('/register/', methods=['GET', 'POST'])
def register_view():
    if request.method == 'GET':
        auth = session.get('email')
        if auth:
            return render_template('yet_auth.html', email=auth)
        return render_template('register.html')

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


@app.route('/login/', methods=['GET', 'POST'])
def login_view():
    if request.method == 'GET':
        auth = session.get('email')
        if auth:
            return render_template('yet_auth.html', email=auth)
        return render_template('login.html', url=request.url)

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
        return render_template('accept.html', **form_values)

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
        'expires': datetime.now() + timedelta(seconds=36000),
        'access_token': generate_token(),
        'refresh_token': generate_token(),
        'token_type': 'Bearer',
        'user': grant['user'],
    }
    mongo.db.OAuth2Access.insert(token)
    mongo.db.OAuth2Code.delete_one({'token': code, 'app': app['client_id']})
    token['expires'] = 36000
    return send_response(request, token)


@app.route('/identify/', methods=['GET'])
def identify_view():
    auth_header = request.headers.environ.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer'):
        return send_error(request, 403)

    token = auth_header[7:]
    grant = mongo.db.OAuth2Access.find({'access_token': token, 'expires': {'$gt': datetime.now()}})
    if grant.count() == 0:
        return send_error(request, 403)

    grant = cursor_to_list(grant)[0]
    user_cursor = mongo.db.user.find({'email': grant['user']})
    if user_cursor.count() != 1:
        return send_error(request, 403)

    user_data = cursor_to_list(user_cursor)[0]
    return send_response(request, {'status': 'OK', 'data': user_data})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9091)

from flask import Flask, request
from flask.ext.pymongo import PyMongo
from lr3_micros.sessions.utils import send_response


app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'sessions_bd'
mongo = PyMongo(app)


@app.route('/register/', methods=['GET', 'POST'])
def register_view():
    if request.method == 'GET':
        return send_response(request, {'status': 'OK'})
    elif request.method == 'POST':
        return send_response(request, {'status': 'OK'})


@app.route('/login/', methods=['GET', 'POST'])
def login_view():
    if request.method == 'GET':
        return send_response(request, {'status': 'OK'})
    elif request.method == 'POST':
        return send_response(request, {'status': 'OK'})


@app.route('/logout/', methods=['GET'])
def logout_view():
    return send_response(request, {'status': 'OK'})


@app.route('/authorize/', methods=['GET', 'POST'])
def authorize_view():
    if request.method == 'GET':
        return send_response(request, {'status': 'OK'})
    elif request.method == 'POST':
        return send_response(request, {'status': 'OK'})


@app.route('/token/', methods=['POST'])
def access_token_view():
    return send_response(request, {'status': 'OK'})


@app.route('/me/', methods=['GET'])
def personal_view():
    return send_response(request, {'status': 'OK'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9091)

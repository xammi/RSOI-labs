from flask import Flask, render_template, redirect, request
from datetime import datetime
import requests
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

key = 'nUAjAEMptUasupE5W4'
secret = 'XZwWS9axc7zFjpxBSwbexVxNg84K3Ywn'
token = 'unknown'

def get_str_date_tyme():
    return datetime.now().strftime("%d.%m.%Y_%Hh.%Mm.%Ss")

path_log = 'C:/bmstu/maga/sem1/rsoi/test1/log/log' + get_str_date_tyme() + '.txt'

def get_none():
    app.logger.info("Use none function!")
    return {'None': 'none'}

def get_me_information():
    headers = {'Authorization': 'Bearer ' + token}
    me_inf = requests.get('https://api.bitbucket.org/2.0/user', headers=headers)
    if (me_inf.status_code == 200):
        app.logger.info("Get me information success: " + me_inf.text)
    else:
        app.logger.error("Error during getting me information!")
    return me_inf.json()

def get_email_information():
    headers = {'Authorization': 'Bearer ' + token}
    email_inf = requests.get('https://api.bitbucket.org/2.0/user/emails', headers=headers)
    if (email_inf.status_code == 200):
        app.logger.info("Get email information success: " + email_inf.text)
    else:
        app.logger.error("Error during getting email information !")
    return email_inf.json()

buttons = [ # список кнопок на выполнение запросов, требующих авторизацию
        {
            'text_b': 'User information',
            'func': get_me_information
        },
        {
            'text_b': 'Email information',
            'func': get_email_information
        }
    ]

def get_request_function(text_b):
    funct = get_none
    for dict in buttons:
        if dict['text_b'] == text_b:
            funct = dict['func']
    return funct

@app.route("/")
@app.route('/index')
def start_page():
    app.logger.info("Index page open!")
    return render_template("index.html",
                           redirect_ref = 'redirect',
                           text_b = 'Авторизоваться через Bitbucket!',
                           text_information = 'Нажмите на кнопку ниже')

@app.route('/ask_information')
def ask_information_page():
    global buttons
    return render_template("ask_information.html",
                           redirect_ref = 'information',
                           buttons = buttons)

@app.route('/information')
def information_page():
    param = request.args.get('Submit')
    req_funct = get_request_function(param)
    current_dict = req_funct()
    return render_template("information.html",
                           list_keys = list(current_dict),
                           dict = current_dict,
                           redirect_ref_back = 'ask_information',
                           text_b_back = 'Вернуться')

@app.route('/redirect')
def redirect_bitbucket():
    app.logger.info("Redirect for request authorization!")
    return redirect("https://bitbucket.org/site/oauth2/authorize?client_id=" + key + "&response_type=code")

@app.route('/authorize')
def auth():
    code = request.args.get('code')
    app.logger.info("Return from request authorization with code: " + code)
    data = {'grant_type': 'authorization_code', 'code': code}
    r = requests.post('https://bitbucket.org/site/oauth2/access_token', data=data, auth=(key, secret))

    if (r.status_code != 200):
        app.logger.error("Error during getting token!")
        return render_template("index.html",
                               redirect_ref='redirect',
                               text_b='Авторизоваться через Bitbucket!',
                               text_information='Ошибка в получении токена! Попробуйте ещё раз позднее!')

    global token
    token = r.json()["access_token"]
    app.logger.info("Get token: " + token)

    return redirect('/ask_information')

if __name__ == '__main__':
    handler = RotatingFileHandler(path_log, maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(20)
    app.run()

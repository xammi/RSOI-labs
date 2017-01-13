from flask import Flask, request
from datetime import datetime
from flask.ext.pymongo import PyMongo, ASCENDING, DESCENDING
from lr3_micros.companies.utils import send_error, send_response, paginate, Error, cursor_to_list

app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'company_bd'
mongo = PyMongo(app)

COMPANY_FIELDS = ['abbreviation', 'name', 'info', 'user']


@app.route('/companies/', methods=['GET'])
def companies_view():
    """
    curl -X GET 'http://localhost:9092/companies/?size=2&page=2'
    """

    find_params = {}
    email = request.headers.environ.get('HTTP_X_EMAIL')
    if email:
        find_params['user'] = email

    try:
        companies = mongo.db.company.find(find_params).sort('created', DESCENDING)
        result = paginate(request, data=companies)
        return send_response(request, result)

    except Error as e:
        return send_error(request, e.code)


@app.route('/company/<abbr>/', methods=['GET', 'PATCH', 'DELETE'])
def get_company_view(abbr):
    """
    curl -X GET 'http://localhost:9092/company/TTS/'
    curl -X PATCH -d '{"info": "Hello"}' -H "Content-Type: application/json" 'http://127.0.0.1:9092/company/TTS/'
    curl -X DELETE 'http://localhost:9092/company/TTS/'
    """

    if request.method == 'GET':
        company = mongo.db.company.find({'abbreviation': abbr})
        company = cursor_to_list(company)
        if len(company) > 0:
            return send_response(request, company[0])
        else:
            return send_error(request, 404)

    elif request.method == 'PATCH':
        #TODO: check owner

        company = {field: request.json.get(field) for field in COMPANY_FIELDS if field in request.json}
        if len(company) == 0:
            return send_error(request, 400)

        company['updated'] = datetime.now()
        result = mongo.db.company.update_one({'abbreviation': abbr}, {'$set': company})
        return send_response(request, {'status': 'OK', 'updated': result.matched_count})

    elif request.method == 'DELETE':
        #TODO: check owner

        result = mongo.db.company.delete_one({'abbreviation': abbr})
        return send_response(request, {'abbreviation': abbr, 'deleted': result.deleted_count})


@app.route('/company/', methods=['POST'])
def create_company_view():
    """
    curl -X POST -H "Content-Type: application/json" 'http://127.0.0.1:9092/company/' \
    -d '{"abbreviation": "TTS", "name": "Transport Travel System", "info": null, "user": "xammi-1@yandex.ru"}'
    """

    #TODO: create with owner

    company = {field: request.json.get(field) for field in COMPANY_FIELDS}
    found = mongo.db.company.find({'abbreviation': company['abbreviation']}).count()
    if found > 0:
        return send_response(request, {'status': 'Such abbr already exists'})

    company['created'] = datetime.now()
    mongo.db.company.insert(company)
    return send_response(request, {'status': 'OK', 'data': company})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9092)

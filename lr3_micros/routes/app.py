from datetime import datetime
from flask import Flask, request
from flask.ext.pymongo import PyMongo, ASCENDING, DESCENDING, ObjectId
from lr3_micros.routes.utils import send_error, send_response, paginate, Error, cursor_to_list
import requests


app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'routes_bd'
mongo = PyMongo(app)

ROUTE_FIELDS = ['name', 'departure', 'arrival', 'locations', 'price', 'company']
COMPANY_SERVICE_URL = 'http://127.0.0.1:9092/'


@app.route('/routes/', methods=['GET'])
def routes_view():
    """
    curl -X get 'http://127.0.0.1:9093/routes/?size=2&page=1'
    """

    try:
        routes = mongo.db.route.find({}).sort('created', DESCENDING)
        result = paginate(request, data=routes)
        return send_response(request, result)

    except Error as e:
        return send_error(request, e.code)


@app.route('/my_routes/', methods=['GET'])
def my_routes_view():
    email = request.headers.environ.get('HTTP_X_EMAIL')
    if not email:
        return send_error(request, 403)

    routes = mongo.db.route.find({'users': email})
    routes = cursor_to_list(routes)
    return send_response(request, {'status': 'OK', 'data': routes})


@app.route('/route/', methods=['POST'])
def create_route_view():
    """
    curl -X POST -H "Content-Type: application/json" 'http://127.0.0.1:9093/route/' \
    -d '{"name": "North Russia", "departure": "2015-10-10 12:00:00", "arrival": "2015-10-15 18:00:00", "price": 100, "company": "TTS"}'
    """

    #TODO: check company owner

    route = {field: request.json.get(field) for field in ROUTE_FIELDS}
    response = requests.get(COMPANY_SERVICE_URL + 'company/' + route['company'])
    if response.status_code == 404:
        return send_error(request, 404)

    route['created'] = datetime.now()
    mongo.db.route.insert(route)
    return send_response(request, {'status': 'OK', 'data': route})


@app.route('/route/<route_id>', methods=['GET', 'PATCH', 'DELETE'])
def get_route_view(route_id):
    """
    curl -X get 'http://127.0.0.1:9093/route/586f956f050df411919ca464'
    curl -X delete 'http://127.0.0.1:9093/route/586f956f050df411919ca464'
    """

    if request.method == 'GET':
        route = mongo.db.route.find({'_id': ObjectId(route_id)})
        route = cursor_to_list(route)
        if len(route) > 0:
            return send_response(request, route[0])
        else:
            return send_error(request, 404)

    elif request.method == 'PATCH':
        #TODO: check company owner

        route = {field: request.json.get(field) for field in ROUTE_FIELDS if field in request.json}
        if len(route) == 0:
            return send_error(request, 400)

        route['updated'] = datetime.now()
        result = mongo.db.route.update_one({'_id': ObjectId(route_id)}, {'$set': route})
        return send_response(request, {'status': 'OK', 'updated': result.matched_count})

    elif request.method == 'DELETE':
        #TODO: check company owner

        result = mongo.db.route.delete_one({'_id': ObjectId(route_id)})
        return send_response(request, {'_id': route_id, 'deleted': result.deleted_count})


@app.route('/route/<route_id>/register/', methods=['POST'])
def register_view(route_id):
    """
    curl -X post 'http://127.0.0.1:9093/route/586f9570050df411919ca465/register/' -H 'X_EMAIL: xammi@yandex.ru' -H 'X_SECRET: ewifyw521763eyuwfgeuwYTWDYA'
    """

    email = request.headers.environ.get('HTTP_X_EMAIL')
    if not email:
        return send_error(request, 404)

    route = mongo.db.route.find({'_id': ObjectId(route_id)})
    if route.count() == 0:
        return send_error(request, 404)

    route = cursor_to_list(route)[0]
    users_on_route = route.get('users', [])
    if email not in users_on_route:
        users_on_route.append(email)
        result = mongo.db.route.update_one({'_id': ObjectId(route_id)}, {'$set': {'users': users_on_route}})
        return send_response(request, {'status': 'OK', 'updated': result.matched_count})
    else:
        return send_response(request, {'status': 'OK', 'updated': 0})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9093)

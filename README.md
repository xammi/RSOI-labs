Третья лабораторная работа по РСОИ. Было проведено разделение монолитного приложения из второй лабораторной на микросервисы.
Первый отвечает за создание, хранение и редактирование туристических компаний. Второй - за создание, хранение и редактирование туристических маршрутов, организуемых компаниями.
Оба сервиса предоставляют соответствующее API, в котором некоторые методы требуют авторизации, а некоторые нет.
Авторизация по oauth2 и хранение данных пользователей реализованы в третьем сервисе (sessions).
Для демонстрации работы приложения написано специальное клиентское приложение: lr3_client.py.

## Prerequisites
python3, flask, MongoDB, pymongo

## Getting started

### launch mongodb
```sh
$ /usr/local/Cellar/mongodb/3.4.0/bin/mongod
```

### launch services
```sh
$ python3 ./lr3_micros/companies/app.py
$ python3 ./lr3_micros/routes/app.py
$ python3 ./lr3_micros/sessions/app.py
```

### create company
```sh
$ curl -X POST -H "Content-Type: application/json" 'http://127.0.0.1:9092/company/' -d '{"abbreviation": "TTS", "name": "Transport Travel System", "info": null, "user": "xammi@yandex.ru"}'
$ curl -X GET 'http://localhost:9092/companies/?size=3&page=1'
```

### create route
```sh
$ curl -X POST -H "Content-Type: application/json" 'http://127.0.0.1:9093/route/' -d '{"name": "North Russia", "departure": "2015-10-10 12:00:00", "arrival": "2015-10-15 18:00:00", "price": 100, "company": "TTS"}'
$ curl -X GET 'http://127.0.0.1:9093/routes/?size=2&page=1'
```

### register user in browser by URL: http://127.0.0.1:9091/register/

### launch client application
```sh
$ python3 ./lr3_client.py
```

### authorize through oauth2 by URL: http://127.0.0.1:9090/
### register on route by query: POST route/586f9570050df411919ca465/register
### take personal info (aggregation query): GET me

### the result is:
```js
{
    "data": {
        "first_name": "Максим",
        "last_name": "Кисленко",
        "created": "Fri, 06 Jan 2017 18:07:39 GMT",
        "_id": "586fb2bb050df416746d3d04",
        "routes": [
            {
                "price": 100,
                "locations": null,
                "company": "TTS",
                "name": "North Russia",
                "created": "Fri, 06 Jan 2017 16:02:40 GMT",
                "_id": "586f9570050df411919ca465",
                "arrival": "2015-10-15 18:00:00",
                "users": [
                    "xammi@yandex.ru"
                ],
                "departure": "2015-10-10 12:00:00"
            }
        ],
        "email": "xammi@yandex.ru",
        "companies": [
            {
                "created": "Sat, 07 Jan 2017 23:22:39 GMT",
                "info": null,
                "abbreviation": "TTS2",
                "name": "Transport Travel System",
                "user": "xammi@yandex.ru"
            }
        ]
    },
    "status": "OK"
}
```
#!/bin/sh
uwsgi --http :8000 --gevent 1000 --http-websockets --master --wsgi-file wsgi_v2.py --callable app

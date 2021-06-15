#!/usr/bin/env python3
import os

bind = '0.0.0.0:8171'
workers = os.environ['GUNICORN_WORKERS'] if 'GUNICORN_WORKERS' in os.environ else 5
preload_app = True


# Server Hooks
def post_fork(server, worker):
    pass

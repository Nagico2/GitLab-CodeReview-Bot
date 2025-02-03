import os
import multiprocessing

preload_app = True
bind = "0.0.0.0:8000"

gunicorn_workers = os.environ.get('GUNICORN_WORKERS', 'auto')

if gunicorn_workers.lower() == 'auto':
    gunicorn_workers = multiprocessing.cpu_count() * 2 + 1

gunicorn_threads = os.environ.get('GUNICORN_THREADS', 'auto')

if gunicorn_threads.lower() == 'auto':
    gunicorn_threads = multiprocessing.cpu_count() * 2

workers = int(gunicorn_workers)
threads = int(gunicorn_threads)
backlog = 2048

worker_class = "gevent"

worker_connections = 1200

proc_name = 'gunicorn.pid'
pidfile = 'app_run.log'
loglevel = 'info'
logfile = 'logs/gunicorn.log'

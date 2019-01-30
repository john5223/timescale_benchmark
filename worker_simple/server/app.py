import os
import logging
from flask import Flask
from flasgger import Swagger

from server.controller import routes, tasks, celery
from server import celeryconfig


logger = logging.getLogger()

def create_app(debug=False):
    return entrypoint(debug=debug, mode='app')

def create_celery(debug=False):
    return entrypoint(debug=debug, mode='celery')

def entrypoint(debug=False, mode='app'):
    assert isinstance(mode, str), 'bad mode type "{}"'.format(type(mode))
    assert mode in ('app','celery'), 'bad mode "{}"'.format(mode)

    app = Flask(__name__)

    app.debug = debug

    configure_app(app)
    configure_logging(debug=debug)
    configure_celery(app, tasks.celery)

    swagger_config = {
        "headers": [
        ],
        "specs": [
            {
                "endpoint": 'specifications',
                "route": '/specifications.json',
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            }
        ],
        "static_url_path": "/flasgger_static",
        # "static_folder": "static",  # must be set by user
        "specs_route": "/docs"
    }

    Swagger(app, config=swagger_config)

    # register blueprints
    app.register_blueprint(routes.bp, url_prefix='')

    if mode=='app':
        return app
    elif mode=='celery':
        return celery

def configure_app(app):
    logger.info('configuring flask app')
    app.config['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL') or os.environ.get('BROKER')
    app.config['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND') or os.environ.get('BROKER')

def configure_celery(app, celery):
    # set celery config from celery_config.py
    celery.config_from_object(celeryconfig)
    # set broker url and result backend from flask app config
    celery.conf.broker_url = app.config['CELERY_BROKER_URL']
    celery.conf.result_backend = app.config['CELERY_RESULT_BACKEND']

    # subclass task base for app context
    # http://flask.pocoo.org/docs/0.12/patterns/celery/
    TaskBase = celery.Task
    class AppContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = AppContextTask

    # run finalize to process decorated tasks
    celery.finalize()

def configure_logging(debug=False):

    root = logging.getLogger()
    h = logging.StreamHandler()
    fmt = logging.Formatter(
        fmt='%(asctime)s %(levelname)s (%(name)s) %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    h.setFormatter(fmt)

    root.addHandler(h)

    if debug:
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)

import os
from kombu import Queue, Exchange

broker = os.environ.get('CELERY_BROKER_URL')
result_backend = os.environ.get('CELERY_RESULT_BACKEND')

task_queues = (
    Queue('QueueA', Exchange('ExchangeA'), routing_key='RouteA'),
    Queue('QueueB', Exchange('ExchangeB'), routing_key='RouteB'),
    Queue('stats', Exchange('stats'), routing_key='stats'),
)
task_default_queue = 'QueueA'
task_default_exchange = 'ExchangeA'
task_default_routing_key = 'RouteA'
task_routes = {
    'task_b': {'queue': 'QueueB'},
    '*': {'queue': 'QueueA'},
}

task_acks_late = True
worker_prefetch_multiplier = 1

TIMESCALEDB_HOST = os.environ.get('TIMESCALEDB_HOST')
POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT')
POSTGRES_DBNAME = os.environ.get('POSTGRES_DBNAME')
POSTGRES_USER = os.environ.get('POSTGRES_USER')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')


'''
# Fast / Slow queue examples
task_queues = (
    Queue('slow', Exchange('slow'), routing_key='slow'),
    Queue('fast', Exchange('fast'), routing_key='fast'),
)
task_default_queue = 'fast'
task_default_exchange = 'fast'
task_default_routing_key = 'fast'
task_routes = {
    'slow_task': {'queue': 'slow'},
    '*': {'queue': 'fast'},
}
'''



#task_annotations = {'tasks.add': {'rate_limit': '10/s'}}

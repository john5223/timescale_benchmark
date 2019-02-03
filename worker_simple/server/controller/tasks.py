"""
Celery.

"""
#import functools
import os
import datetime
import time
import logging
import psycopg2

from celery import Celery
from celery import group, chord

from server.controller.db import PostgresTask
from server.controller.db import TimescaleTask

from server.controller.db import SQLAlchemyTask
from server.controller.db import TimescaleAlchemyTask



logger = logging.getLogger()
celery = Celery(__name__, autofinalize=False)

class UnknownDB(Exception):
    pass


def query_stats(csv=None, db=None, client=None, loadbalance=None, number_runs=None):
    if not number_runs:
        number_runs = 1
    if not db:
        db = "timescaledb"
    logger.info(client)
    if client is None:
        client = "psycopg2"
        #client = "sqlalchemy"

    cpu_stats = None
    if db == "postgres":
        if client == "psycopg2":
            cpu_stats = postgres_cpu_stats
        elif client == "sqlalchemy":
            cpu_stats = sqlalchemy_cpu_stats

    elif db == "timescaledb":
        if client == "psycopg2":
            cpu_stats = timescaledb_cpu_stats
        elif client == "sqlalchemy":
            cpu_stats = timescalealchemy_cpu_stats
    else:
        raise UnknownDB(db)
    logger.info("Database: {}".format(db))
    logger.info("Client: {}".format(client))

    csv = csv.split('\n')
    # Figure out queues for load balancing
    QUEUE_NAMES = None
    MAX_QUEUE_INDEX = 0
    if celery.conf.task_queues:
        QUEUE_NAMES = [x.name for x in celery.conf.task_queues if 'stats' not in x.name]
        MAX_QUEUE_INDEX = len(QUEUE_NAMES) - 1
        logger.info(QUEUE_NAMES)

    # TODO: Should we have form data set this too?
    LOADBALANCE_KEY = 'hostname'
    # TODO: move this lookup to redis queue so all worker instances
    # will send to the same queue/exchange
    # (if needed)
    LOADBALANCE_KEY_LOOKUP = {}
    queue_index = 0

    # Start creating tasks
    logger.info('start task...')
    headers = None
    tasks = []
    for row in csv:
        if not headers:
            headers = row.split(',')
        elif row:
            row = row.split(',')
            row_data = {x: row[i] for i, x in enumerate(headers)}
            # route based on hostname roundrobin to the exchanges
            task = None
            if loadbalance:
                # pick the queue based on the LOADBALANCE_KEY
                # to keep the tasks on the same queue
                # (and therfore the same worker if setup properly)
                key = row_data[LOADBALANCE_KEY]
                queue_name = LOADBALANCE_KEY_LOOKUP.get(key)
                if not queue_name:
                    queue_name = QUEUE_NAMES[queue_index]
                    queue_index = queue_index + 1
                    if queue_index > MAX_QUEUE_INDEX:
                        queue_index = 0
                    LOADBALANCE_KEY_LOOKUP[key] = queue_name
                task = cpu_stats.signature(kwargs={'data': row},
                                           queue=queue_name)
            else:
                task = cpu_stats.signature(kwargs={'data': row})
            tasks.append(task)

            if len(tasks) > 8:
                break

    # Docs for groups and chords within celery are here:
    # http://docs.celeryproject.org/en/latest/userguide/canvas.html#groups
    job = group(tasks * number_runs)
    stats = task_query_stats.signature(kwargs={'db': db}, options={'queue': 'stats'})
    chord_task = chord(job)(stats)
    return chord_task


@celery.task(bind=True, soft_time_limit=600)
def task_query_stats(self, task_results, db=None):
    task_runtimes, task_results = zip(*task_results)
    logger.info(task_runtimes)

    try:
        import numpy as np
        from scipy import stats

        task_runtimes = np.array(task_runtimes)
        runtime_stats = stats.describe(task_runtimes)
        logger.info(runtime_stats)

        ret = runtime_stats._asdict()
        ret['total_querytime'] = task_runtimes.sum()
        ret['db'] = db
        return ret

    except ImportError as e:

        return {
            'min': min(task_runtimes),
            'max': max(task_runtimes),
            'avg': avg(task_runtimes)
        }

def query_cpu_stats(cursor, data):
    # measure query time here so only measure
    # the database query and not celery
    task_start = datetime.datetime.now()
    host, start, end = data
    q = ('SELECT avg(usage) '
         'FROM cpu_usage '
         'WHERE host = %s AND ts > %s and ts < %s')
    logger.info(q)
    cursor.execute(q, (host, start, end,))
    result = cursor.fetchone()
    task_time = (datetime.datetime.now() - task_start).total_seconds()
    return (task_time, result,)


def sqlalchemy_query_cpu_stats(db_session, data):
    task_start = datetime.datetime.now()
    #host, start, end = data
    params = {
        'host': data[0],
        'start': data[1],
        'end': data[2]
    }
    q = ('SELECT avg(usage) '
         'FROM cpu_usage '
         'WHERE host = :host AND ts > :start and ts < :end')
    logger.info(q)
    result = db_session.execute(q, params).fetchone()
    result = result.items()
    if result:
        result = result[0][1]
    task_time = (datetime.datetime.now() - task_start).total_seconds()
    return (task_time, result,)


@celery.task(base=PostgresTask, bind=True, soft_time_limit=600)
def postgres_cpu_stats(self, data):
    logger.info("Postgres query")
    cursor = self.db.cursor()
    result = query_cpu_stats(cursor, data)
    return result


@celery.task(base=TimescaleTask, bind=True, soft_time_limit=600)
def timescaledb_cpu_stats(self, data):
    logger.info("Timescaledb query")
    cursor = self.db.cursor()
    result = query_cpu_stats(cursor, data)
    return result


@celery.task(base=SQLAlchemyTask, bind=True, soft_time_limit=600)
def sqlalchemy_cpu_stats(self, data):
    logger.info("Sqlalchemy query")
    result = sqlalchemy_query_cpu_stats(self.db_session, data)
    return result

@celery.task(base=TimescaleAlchemyTask, bind=True, soft_time_limit=600)
def timescalealchemy_cpu_stats(self, data):
    logger.info("Timescale sqlalchemy query")
    result = sqlalchemy_query_cpu_stats(self.db_session, data)
    return result

@celery.task(bind=True)
def wait_task(self, sleep_time):
    '''sample task that sleeps 5 seconds then returns the current datetime'''
    time.sleep(sleep_time)
    return datetime.datetime.now().isoformat()

@celery.task(bind=True)
def add(self, a, b):
    x = 5
    self.update_state(state="Processing", meta="Waiting for loop")
    while x > 0:
        x = x - 1
        time.sleep(2)
    return a+b


'''

OPTION 1:
##############3

from time import time
from celery.signals import task_prerun, task_postrun


tasks = {}
task_avg_time = {}
Average = namedtuple('Average', 'cum_avg count')


@task_prerun.connect
def task_prerun_handler(signal, sender, task_id, task, args, kwargs):
    tasks[task_id] = time()


@task_postrun.connect
def task_postrun_handler(signal, sender, task_id, task, args, kwargs, retval, state):
    try:
        cost = time() - tasks.pop(task_id)
    except KeyError:
        cost = None

    if not cost:
        return

    try:
        cum_avg, count = task_avg_time[task.name]
        new_count = count + 1
        new_avg = ((cum_avg * count) + cost) / new_count
        task_avg_time[task.name] = Average(new_avg, new_count)
    except KeyError:
        task_avg_time[task.name] = Average(cost, 1)

    # write to redis: task_avg_time




OPTION 2:
##############


def timeit(func):
    """A decorator used to log the function execution time."""
    logger = logging.getLogger('tasks')

    # Use functools.wraps to ensure function name is not changed
    # http://stackoverflow.com/questions/13492603/celery-task-with-multiple-decorators-not-auto-registering-task-name
    @functools.wraps(func)
    def wrap(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        dur = time.time() - start
        msg = {
            'task_name': func.__module__ + '.' + func.__name__,
            'duration': dur,

            # Use 'task_args' instead of 'args' because 'args' conflicts with
            # attribute of LogRecord
            'task_args': args,
            'task_kwargs': kwargs
        }
        logger.info('%s %.2fs', func.__name__, dur, extra=msg)
        return result

    return wrap


def shared_task(*args, **kwargs):
    """Override Celery's default shared_task decorator to log every task call.
    """
    import pdb; pdb.set_trace()
    if len(args) == 1 and callable(args[0]):
        func = args[0]
        return orig_shared_task(**kwargs)(timeit(func))

    def decorator(func):
        return orig_shared_task(*args, **kwargs)(timeit(func))

    return decorator

'''
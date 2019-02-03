
Database Query Statistics
================================

Gets the statistics for queries run in celery tasks.

Min, max, avg runtime of query that is run inside celery task.

Querying timescaledb and postgres for cpu_usage average over different time intervals.

Columns of data are: hostname, timestamp, cpu_usage

This project sets up a flask api to run tasks to query postgres/timescaledb database. Queries are generated from a csv input file of timestamps to query an average for. Time it takes to query database is returned from the task and aggregated inside a different worker.

Docker containers:

	- api
	- worker_QueueA
	- worker_QueueB
	- worker_stats

Task Broker:

	- redis

Task Worker:

	- celery

Workflows:

	- celery
	- (in the future) airflow


Celery workers can either use process pools, thread pools, or eventlet pools.

Threads or processes for cpu bound tasks.
Network IO tasks (like database queries) can use eventlet pools.

TODO: get psycopgreen working with celery tasks to use -P eventlet or -P gevent


Usage
=========

To get environment up and running use the command:

	make dev

Once docker containers are built via docker-compose then you can
POST data to /cpu/stats with the form parameters as follows:

- data = your query_params.csv file for generating queries
- number_runs = number of times you want to duplicate the tasks created
- db = set to either postgres or timescaledb
- wait_for_return = set to true to get results returned or default is false which returns immediately and you have to poll cpu_stats/<task_id> for results


Example:

	福 curl -X POST -F 'data=@data/query_params.csv' -F "number_runs=10" -F "wait_for_return=True" -F "db=postgres" localhost:5000/cpu_stats
	{
	  "db": "postgres",
	  "number_runs": 10,
	  "result": {
	    "kurtosis": 1.1310037343955148,
	    "mean": 0.077074878,
	    "minmax": [
	      0.020368,
	      0.204731
	    ],
	    "nobs": 2000,
	    "skewness": 0.8921114157233603,
	    "total_querytime": 154.149756,
	    "variance": 0.0007089277304803561
	  },
	  "state": "SUCCESS",
	  "task_id": "2c7feb83-5500-4274-a898-e8adb74f16be"
	}


	福 curl -X POST -F 'data=@data/query_params.csv' -F "number_runs=10" -F "wait_for_return=True" -F "db=timescaledb" localhost:5000/cpu_stats
	{
	  "db": "timescaledb",
	  "number_runs": 10,
	  "result": {
	    "kurtosis": 8.55457982291601,
	    "mean": 0.009513939499999999,
	    "minmax": [
	      0.004814,
	      0.04515
	    ],
	    "nobs": 2000,
	    "skewness": 1.9600806771624373,
	    "total_querytime": 19.027879,
	    "variance": 1.1452820913296399e-05
	  },
	  "state": "SUCCESS",
	  "task_id": "5056fc5e-bef6-403e-b768-44043c546421"
	}


Stats are generated from :

https://github.com/john5223/timescale_benchmark/blob/master/worker_simple/server/controller/tasks.py#L99

Flower is running on http://localhost:5555 which will show running tasks.


Results
========

Timescaledb can do in 19 seconds what postgres takes 154 seconds to complete.

Nice! Auto time scaled partitions are awesome!



TODO
=====

Seperate numpy worker and lightweight worker from the api (Dockerfile)

Call tasks using signatures instead of importing the tasks from the api.

Do this so we can have small api container, small worker container, and heavy numpy worker container seperate so we can scale them differently.

Try and build a golang worker than integrates with celery / airflow (don't want to reinvent the wheel)


## Links

https://medium.com/@taylorhughes/three-quick-tips-from-two-years-with-celery-c05ff9d7f9eb

https://github.com/rochacbruno/flasgger/blob/master/examples//example_app.py

https://github.com/mattkohl/docker-flask-celery-redis

http://www.prschmid.com/2013/04/using-sqlalchemy-with-celery-tasks.html

https://github.com/zenyui/celery-flask-factory

https://github.com/nickjj/build-a-saas-app-with-flask

https://github.com/epwalsh/docker-celery

https://github.com/NodeRedis/node_redis

https://github.com/William-Yeh/nodejs-redis-example

https://github.com/yesuagg/redis-sentinel-cluster

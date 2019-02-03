
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


	desktop 福 ~/git/john/timescale_benchmark ➤ 08d5528|master⚡
	249 ± : curl -X POST -F 'data=@data/query_params.csv' -F "number_runs=7" -F "wait_for_return=True" -F "db=postgres" -F "client=sqlalchemy" localhost:5000/cpu_stats

	{
	  "db": "postgres",
	  "endpoint": "http://localhost:5000/cpu_stats/8097ef44-6f0b-4d5e-bcec-cd04e529197e",
	  "number_runs": 7,
	  "result": {
	    "kurtosis": 0.9745369709248504,
	    "mean": 0.28278166285714285,
	    "minmax": [
	      0.065737,
	      0.793913
	    ],
	    "nobs": 1400,
	    "skewness": 0.9399346706621935,
	    "total_querytime": 395.894328,
	    "variance": 0.01198067500476402
	  },
	  "state": "SUCCESS",
	  "task_id": "8097ef44-6f0b-4d5e-bcec-cd04e529197e"
	}


	desktop 福 ~/git/john/timescale_benchmark ➤ 08d5528|master⚡
	250 ± : curl -X POST -F 'data=@data/query_params.csv' -F "number_runs=7" -F "wait_for_return=True" -F "db=postgres" -F "client=psycopg2" localhost:5000/cpu_stats

	{
	  "db": "postgres",
	  "endpoint": "http://localhost:5000/cpu_stats/c754cfcb-0067-4f09-bc48-10fa255f579b",
	  "number_runs": 7,
	  "result": {
	    "kurtosis": 0.43178245703551044,
	    "mean": 0.2817891707142857,
	    "minmax": [
	      0.060597,
	      0.816402
	    ],
	    "nobs": 1400,
	    "skewness": 0.8219990308126535,
	    "total_querytime": 394.504839,
	    "variance": 0.013859435964148818
	  },
	  "state": "SUCCESS",
	  "task_id": "c754cfcb-0067-4f09-bc48-10fa255f579b"
	}


	desktop 福 ~/git/john/timescale_benchmark ➤ 08d5528|master⚡
	251 ± : curl -X POST -F 'data=@data/query_params.csv' -F "number_runs=7" -F "wait_for_return=True" -F "db=timescaledb" -F "client=psycopg2" localhost:5000/cpu_stats

	{
	  "db": "timescaledb",
	  "endpoint": "http://localhost:5000/cpu_stats/96ad62c0-f1e1-4538-9691-3ccba92067b9",
	  "number_runs": 7,
	  "result": {
	    "kurtosis": 0.5540491207683771,
	    "mean": 0.06270433714285714,
	    "minmax": [
	      0.008559,
	      0.206954
	    ],
	    "nobs": 1400,
	    "skewness": 0.783589606602244,
	    "total_querytime": 87.78607199999999,
	    "variance": 0.0010947982948626652
	  },
	  "state": "SUCCESS",
	  "task_id": "96ad62c0-f1e1-4538-9691-3ccba92067b9"
	}

	desktop 福 ~/git/john/timescale_benchmark ➤ 08d5528|master⚡
	273 ± : curl -X POST -F 'data=@data/query_params.csv' -F "number_runs=7" -F "wait_for_return=True" -F "db=timescaledb" -F "client=sqlalchemy" localhost:5000/cpu_stats

	{
	  "client": "sqlalchemy",
	  "db": "timescaledb",
	  "endpoint": "http://localhost:5000/cpu_stats/4cdfdd8a-88f4-40bf-afed-01302b88c5ec",
	  "number_runs": 7,
	  "result": {
	    "kurtosis": 6.789417276941661,
	    "mean": 0.008490127142857143,
	    "minmax": [
	      0.00278,
	      0.044303
	    ],
	    "nobs": 1400,
	    "skewness": 2.1486667352394404,
	    "total_querytime": 11.886178,
	    "variance": 2.3671069736503624e-05
	  },
	  "state": "SUCCESS",
	  "task_id": "4cdfdd8a-88f4-40bf-afed-01302b88c5ec"
	}



Flower is running on http://localhost:5555 which will show running tasks.

Results
========

Experiment 1:

	data file:     data/query_params.csv
	number_runs:   7

	Total run time in seconds:

	Postgres with psycopg2      =    394.504839
	Postgres with sqlalchemy    =    395.894328

	Timescaledb with psycopg2   =    87.7860719
	Timescaledb with sqlalchemy =    11.8861780


Timescaledb beats postgres.

Even further speed up when using sqlalchemy over psycopg2 due to the free connection pooling provided by sqlalchemy.

Auto time scaled paritions are awesome!



TODO
=====

Seperate numpy worker and lightweight worker from the api (Dockerfile)

Call tasks using signatures instead of importing the tasks from the api.

Do this so we can have small api container, small worker container, and heavy numpy worker container seperate so we can scale them differently.

Try and build a golang worker than integrates with celery / airflow (don't want to reinvent the wheel)


## Links

https://www.topsqlblogs.com/

https://github.com/OmniDB/OmniDB

https://blog.2ndquadrant.com/pg-phriday-getting-rad-docker/

https://blog.2ndquadrant.com/pg-phriday-getting-rad-docker-part-2/

https://blog.2ndquadrant.com/pg-phriday-getting-rad-docker-part-3/

https://blog.2ndquadrant.com/pg-phriday-getting-rad-docker-part-4/

https://github.com/brainsam/pgbouncer


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

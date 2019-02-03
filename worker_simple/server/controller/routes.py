import logging
from flask import Flask, flash, jsonify, Blueprint
from flask import request
from server.controller import tasks
from server.controller.tasks import UnknownDB

from flasgger.utils import swag_from

bp = Blueprint('tasks', __name__)
logger = logging.getLogger()

@bp.route('/')
def view_base():
    return """
      <h1> Welcome to task demo app</h1>
      This app has one current API version
      <ul>
         <li><a href="/docs">Api Version 1</a></li>
      </ul>
    <p>
      As you can see the APIs is served by the same swagger UI on
      <a href="/docs/index.html">Api docs</a>
     </p>
    """
    # OR
    #return jsonify({'status': 'success'})


@bp.route('/cpu_stats', methods=['POST'])
def view_start_cpu_query():
    """
    CPU Stats
    Get the cpu stats by giving us a csv list of data you want.
    ---
    tags:
      - cpu_stats
    consumes:
      - multipart/form-data  # and/or application/x-www-form-urlencoded
    parameters:
      - in: header
        name: X-Count
        description: The number of times to run the query (for benchmarking)
        schema:
          type: string
      - in: header
        name: X-Request-ID
        schema:
          type: string
          format: uuid
        required: false
      - in: header
        name: number_runs
        description: The number of times to run the same queries (to increase load for benchmark)
        schema:
          type: string
          format: uuid
        required: false
      - in: header
        name: db
        description: Which db to run against (timescaledb or postgres)
        schema:
          type: string
          format: uuid
        required: false
      - in: formData
        name: data
        type: file
        description: The file to upload.
    responses:
      200:
        description: Task created.
        schema:
          id: task_response
          properties:
            task_id:
              type: integer
              description: The id of the task
              default: 1
      204:
         description: No task submitted.
    """
    if 'data' not in request.files:
        flash('No file part')
        return redirect(request.url)

    request_file = request.files['data']
    csv = str(request_file.read(), 'utf-8')
    if not csv:
        jsonify({
            'status': 'error',
            'error': 'No data passed',
        }), 400

    # TODO: validate csv file (or in task)
    # ...

    kwargs = {
      'csv': csv,
      'db': request.form.get('db', 'timescaledb'),
      'loadbalance': request.form.get('loadbalance', True),
      'number_runs': int(request.form.get('number_runs', 1))
    }
    try:
        task = tasks.query_stats(**kwargs)
    except UnknownDB as e:
        return jsonify({"status": "error", "error": "Unknown database: {}".format(e)}), 400

    logger.info('return task...')
    ret = {
        'task_id': task.id,
        'state': task.state,
        'number_runs': kwargs['number_runs'],
        'endpoint': request.url + "/" + task.id
    }

    wait_for_return = request.form.get('wait_for_return') in ['true', 'True']
    if wait_for_return:
        ret['result'] = task.get()
        ret['db'] = ret['result'].pop('db', None)
        ret['state'] = task.state
    return jsonify(ret), 202


@bp.route('/cpu_stats/<task_id>', methods=['GET'])
def view_check_cpu_stats_task(task_id):
    '''return task state'''
    task = tasks.task_query_stats.AsyncResult(task_id)
    output = {'task_id': task.id, 'state': task.state}
    if task.state == 'SUCCESS':
        output.update({'result': task.result})
    return jsonify(output)

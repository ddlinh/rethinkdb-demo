import argparse
import json

from flask import Flask, g, jsonify, render_template, request, abort
from rethinkdb import r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

HOST =  'localhost'
PORT = 28015
TODO_DB = 'todoapp'


def dbSetup():
    connection = r.connect(host=HOST, port=PORT)
    try:
        r.db_create(TODO_DB).run(connection)
        r.db(TODO_DB).table_create('todos').run(connection)
        print ('Database setup completed. Now run the app without --setup.')
    except RqlRuntimeError:
        print ('App database already exists. Run the app without --setup.')
    finally:
        connection.close()


app = Flask(__name__)
app.config.from_object(__name__)


@app.before_request
def before_request():
    try:
        g.rdb_conn = r.connect(host=HOST, port=PORT, db=TODO_DB)
    except RqlDriverError:
        abort(503, "No database connection could be established.")

@app.teardown_request
def teardown_request(exception):
    try:
        g.rdb_conn.close()
    except AttributeError:
        pass


#### Listing existing todos
@app.route("/todos", methods=['GET'])
def get_todos():
    selection = list(r.table('todos').run(g.rdb_conn))
    return json.dumps(selection)

#### Creating a task
@app.route("/todos", methods=['POST'])
def new_todo():
    inserted = r.table('todos').insert(request.json).run(g.rdb_conn)
    return jsonify(id=inserted['generated_keys'][0])


#### Retrieving a single todo
@app.route("/todos/<string:todo_id>", methods=['GET'])
def get_todo(todo_id):
    todo = r.table('todos').get(todo_id).run(g.rdb_conn)
    return json.dumps(todo)

#### Editing/Updating a task
@app.route("/todos/<string:todo_id>", methods=['PUT'])
def update_todo(todo_id):
    return jsonify(r.table('todos').get(todo_id).replace(request.json).run(g.rdb_conn))

#### Deleting a task
@app.route("/todos/<string:todo_id>", methods=['DELETE'])
def delete_todo(todo_id):
    return jsonify(r.table('todos').get(todo_id).delete().run(g.rdb_conn))

#show mainpage
@app.route("/")
def show_todos():
    return render_template('todo.html')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Flask todo app')
    parser.add_argument('--setup', dest='run_setup', action='store_true')

    args = parser.parse_args()
    if args.run_setup:
        dbSetup()
    else:
        app.run(debug=True)
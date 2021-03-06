#!/usr/bin/python3
import os
import uuid
from ruamel.yaml import YAML
yaml = YAML()
from flask import Flask, request, session, g, flash, url_for, render_template, redirect
from flask_socketio import SocketIO, emit
from request_handling import handle_request
from data_handling import MQTTLogger, Database

ROOT = os.path.abspath(os.path.dirname(__file__))
SETTINGS_PATH = ROOT + "/config.yaml"


app = socketio = None


def set_globals(_app, _socketio):
    global app
    global socketio
    app, socketio = _app, _socketio


def unique_id():
    return hex(uuid.uuid4().time)[2:-1]


def get_settings(path=SETTINGS_PATH):
    if os.path.isfile(path):
        with open(path, "r") as file_handle:
            return yaml.load(file_handle)
    else:
        with open(path, "w", encoding='utf8') as file_handle:
            print("Creating new settings at %s" % path)
            server = input("Enter a server address to connect to\n")
            port = int(input("Enter a corresponding port [1883]\n") or 1883)
            topics = input("Enter a topics to subscribe to (comma separated)\n")
            username = input("Enter a username for login\n")
            password = input("Enter a password (careful, stored as clear text)\n")
            topics = [t.strip() for t in topics.split(",")]
            yaml.dump(dict(mqtt_settings=dict(server=server, port=port),
                           graphs=dict(graph={topic: {'topic': topic} for topic in topics}),
                           web_settings=dict(host="0.0.0.0", port=3000, username=username, password=password)),
                      file_handle)
            print("*********************************************************************************")
            print("Settings file created. Open %s to edit further details to your preference." % path)
            print("If you'd like to store the data to disk, add a db_path: <filepath> to your config")
            print("*********************************************************************************")
        return get_settings(path)


def setup_greeting(app, graphs):
    @app.route('/')
    def index():
        return render_template('index.html' if (session.get('logged_in') or (not app.config['ADMIN_PASSWORD'])) else 'login.html', graphs=graphs)

    @app.route('/login', methods=['GET', 'POST'])
    @handle_request()
    def login():
        with app.app_context():
            if session.get('logged_in'):
                g.logged_in = True
                flash("You are already logged in")
                return redirect(url_for('index'))
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                if username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']:
                    session['logged_in'] = True
                    session['logged_in_user'] = username
                    g.logged_in = True
                    flash("Successfully logged in")
                    return redirect(url_for('index'))
                else:
                    flash("Those credentials were incorrect")
            return render_template('login.html')

    @app.route('/logout')
    @handle_request()
    def logout():
        if session.get('logged_in'):
            session['logged_in'] = False
            g.logged_in = False
            flash("Successfully logged out")
        else:
            flash("You weren't logged in to begin with")
        return redirect(url_for('index'))


def view_update_event(name, view, data, graph_id):
    room = "%s/%s" % (name, view)
    print("event update for %s" % room)
    with app.test_request_context():
        socketio.emit("%s_view_update" % graph_id,
                      data=dict(data=data, name=name, graph=graph_id, resolution=view), broadcast=True)


def setup(app, socketio, mqtt_settings, graphs, **kwargs):
    set_globals(app, socketio)
    setup_greeting(app, graphs)

    @app.route('/graph')
    @handle_request(private=True if app.config['ADMIN_PASSWORD'] else False)
    def graph():
        graph_name = request.args.get("name")
        return render_template("graph.html", name=graph_name, graph=graphs[graph_name])

    @app.route('/graphs')
    @handle_request(private=True if app.config['ADMIN_PASSWORD'] else False)
    def graphs_overview():
        return render_template("graphs.html", graphs=graphs)

    server, port = mqtt_settings["server"], mqtt_settings["port"]

    data_loggers = {}

    for graph_name, graph_def in graphs.items():

        db_path_parts = mqtt_settings.get("db_path").split(".")
        db_path = ".".join(db_path_parts[:-1]) + graph_name.replace(" ","_").lower() + "." + db_path_parts[-1]
        db = Database(path=db_path)
        mqtt_logger = MQTTLogger(server=server, port=port, graph_def=graph_def, db=db,
                                 on_view_update=view_update_event, id=graph_name)
        data_loggers[graph_name] = mqtt_logger

    @app.route('/data', methods=['GET'])
    @handle_request(format_response=True, private=True if app.config['ADMIN_PASSWORD'] else False)
    def data():
        name = request.args.get("graph_name")
        res = request.args.get("resolution", None)
        return data_loggers[name].get_data_view(resolution=res)

    @socketio.on('connected')
    def handle_connected(json):
        print("connected: "+str(json))

    @socketio.on('message')
    def handle_msg(json):
        print("message: "+str(json))

    @socketio.on('view_update')
    def handle_my_custom_event(json):
        print('received event update for: ' + str(json))


SECRET_KEY = '\xa3\xb6\x15\xe3E\xc5\x8c\xbaT\x14\xd1:\xafc\x9c|.\xc0H\x8d\xf2\xe5\xbd\xd5'

if __name__ == '__main__':
    settings = get_settings()

    app = Flask(__name__, static_url_path='', static_folder='static')
    app.secret_key = SECRET_KEY
    app.config['SESSION_TYPE'] = 'memcache'
    app.config['ADMIN_USERNAME'] = settings["web_settings"]["username"]
    app.config['ADMIN_PASSWORD'] = settings["web_settings"]["password"]

    socketio = SocketIO(app, async_mode='gevent', logger=True, engineio_logger=True)
    setup(app, socketio, **settings)

    socketio.run(app, settings["web_settings"]["host"],
                 port=settings["web_settings"]["port"], debug=True, use_reloader=False)

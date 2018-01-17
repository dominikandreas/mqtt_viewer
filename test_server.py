import os
import sys
from ruamel.yaml import YAML
yaml = YAML()
from flask import Flask
from flask_socketio import SocketIO
from server import SECRET_KEY, setup
ROOT = os.path.abspath(os.path.dirname(__file__))


assert len(sys.argv) > 1
server = sys.argv[-1]

test_settings = """
mqtt_settings:
  port: 1883
  server: %s


graphs:
  Oven:
    'Oven Temp':
      topic: test_topic
      json_template: '{{ oven_temp }}'
    'Meat Temp':
      topic: test_topic
      json_template: '{{ meat_temp }}'
      
  Meat:
    'Meat Temp':
      topic: test_topic
      json_template: '{{ meat_temp }}'
      
  Oven2:
    'Oven Temp':
      topic: test_topic
      json_template: '{{ oven_temp }}'
    'Meat Temp':
      topic: test_topic
      json_template: '{{ meat_temp }}'
      
  Meat2:
    'Meat Temp':
      topic: test_topic
      json_template: '{{ meat_temp }}'
  Oven3:
    'Oven Temp':
      topic: test_topic
      json_template: '{{ oven_temp }}'
    'Meat Temp':
      topic: test_topic
      json_template: '{{ meat_temp }}'
      
  Meat4:
    'Meat Temp':
      topic: test_topic
      json_template: '{{ meat_temp }}'
      
  Oven4:
    'Oven Temp':
      topic: test_topic
      json_template: '{{ oven_temp }}'
    'Meat Temp':
      topic: test_topic
      json_template: '{{ meat_temp }}'
      
  Meat5:
    'Meat Temp':
      topic: test_topic
      json_template: '{{ meat_temp }}'
""" % server


if __name__ == '__main__':
    settings = yaml.load(test_settings)
    if os.path.isfile("./Oven.db"):
        os.remove("./Oven.db")
    app = Flask(__name__, static_url_path='', static_folder='static')
    app.secret_key = SECRET_KEY
    app.config['SESSION_TYPE'] = 'memcache'
    app.config['ADMIN_USERNAME'] = "admin"
    app.config['ADMIN_PASSWORD'] = "admin123"

    socketio = SocketIO(app, async_mode='gevent', logger=True, engineio_logger=True)
    setup(app, socketio, **settings)
    socketio.run(app, host="0.0.0.0",
                 port=3000, debug=True, use_reloader=False)



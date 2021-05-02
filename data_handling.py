from datetime import datetime
import numpy as np
import json
import time
import os
import traceback
import pickle
import jinja2
import logging
from paho.mqtt.client import MQTTMessage, Client as MQTTClient
from apscheduler.schedulers.background import BackgroundScheduler

ROOT = os.path.abspath(os.path.dirname(__file__))
DB_PATH = ROOT + "/data.db"
AVAILABLE_APIS = []

ts = time.time()
utc_offset = (datetime.fromtimestamp(ts) - datetime.utcfromtimestamp(ts)).seconds
logging.info("utc_offset: ", utc_offset)


class Database:
    def __init__(self, path=DB_PATH):
        self.path = path
        self.db = {}
        self.load()
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.save, 'interval', seconds=3)
        self.scheduler.start()

    def get(self, key, default=None):
        return self.db.get(key, default)

    def __getitem__(self, item):
        return self.db.__getitem__(item)

    def __setitem__(self, key, value):
        return self.db.__setitem__(key, value)

    def load(self):
        if self.path is not None:
            if os.path.isfile(self.path):
                with open(self.path, "rb") as f:
                    self.db = pickle.load(f)

    def save(self):
        if self.path is not None:
            try:
                if os.path.isfile(self.path):
                    os.rename(self.path, self.path+".bak")
                with open(self.path, "wb") as f:
                    pickle.dump(self.db, f)
            except:
                traceback.print_exc()

    def __exit__(self, exc_type, exc_value, tb):
        self.scheduler.shutdown()
        del self.scheduler


mqtt_success_codes = {
    0: 'CONNACK_ACCEPTED',
    1: 'CONNACK_REFUSED_PROTOCOL_VERSION',
    2: 'CONNACK_REFUSED_IDENTIFIER_REJECTED',
    3: 'CONNACK_REFUSED_SERVER_UNAVAILABLE',
    4: 'CONNACK_REFUSED_BAD_USERNAME_PASSWORD',
    5: 'CONNACK_REFUSED_NOT_AUTHORIZED'}


class MQTTLogger:
    def __init__(self, server, graph_def, db, port=1883, history_size=600, on_view_update=None, id=None):
        self.db = db
        self.db["histories"] = self.db.get("histories", {})
        self.history_size = history_size
        self.resolutions = ("raw", 0), ("seconds", 1), ("minutes", 60), ("hours", 60 * 60), ("days", 60 * 60 * 24)
        super().__init__()

        self.graph_def = {name: {"topic": entry["topic"],
                                 "template": (jinja2.Template(entry["json_template"])
                                              if "json_template" in entry else None)}
                          for name, entry in graph_def.items()}
        self.topics = list(set([entry["topic"] for entry in self.graph_def.values()]))
        self.on_view_update = on_view_update
        self.client = MQTTClient()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(server, port, 60)
        self.client.loop_start()
        self.id = id

    @property
    def histories(self):
        return self.db["histories"]

    def update_resolutions(self, name, history):
        # update resolution scales each using the finer resolution as input
        resolutions = self.resolutions
        raw_id = self.resolutions[0][0]
        # first, run the update for the raw data
        self.on_view_update(name, raw_id, history[raw_id][-1], self.id)
        for (target_res, time_diff), (source_res, _) in zip(resolutions[1:], resolutions[:-1]):
            source_res, data = history.get(source_res), history.get(target_res, [])
            if len(data) > 0:
                if source_res[-1][0] > data[-1][0] + time_diff * 1000:
                    # new data for is all data from the finer resolution that is newer than the last entry
                    new_data = [s for s in source_res if s[0] > data[-1][0]]
                    # new data point is a tuple of the mean time and mean value (x, y) of this new data
                    data.append(tuple(np.mean(new_data, axis=0)))
                    # crop away data points that are beyond the maximum history size
                    history[target_res] = data[-self.history_size:]
                    # run the view update on the last element that was added to this resolutions history
                    self.on_view_update(name, target_res, history[target_res][-1], self.id)
            else:
                history[target_res] = [source_res[0]]
                self.on_view_update(name, target_res, history[target_res][-1], self.id)

    def log(self, **entries):
        for name, value in entries.items():
            history = self.histories.get(name, {})
            data = history.get("raw", [])
            data.append([(time.time() + utc_offset) * 1000, value])
            history["raw"] = data[-self.history_size:]
            self.update_resolutions(name, history)
            self.histories[name] = history

    @staticmethod
    def parse_payload(payload, template: jinja2.Template) -> float:
        data = json.loads(payload.decode("utf-8"))
        return float(data if template is None else template.render(**data))

    def on_message(self, client, userdata, msg: MQTTMessage):
        try:
            self.log(**{name: self.parse_payload(msg.payload, template=entry["template"])
                        for name, entry in self.graph_def.items() if msg.topic == entry['topic']})
        except Exception as e:
            traceback.print_exc()

    def on_connect(self, client, userdata, flags, rc: int):
        print("Connected with result code " + mqtt_success_codes.get(rc, "unknown"))
        for topic in self.topics:
            client.subscribe(topic)

    def get_data_view(self, resolution="second"):
        time_records = [[d[0] for d in entry[resolution]] for entry in self.histories.values()]
        t_min = np.max([recs[0] for recs in time_records]) if time_records else 0

        return [{"name": name, "data": [d for d in data[resolution] if d[0] >= t_min]}
                for name, data in self.histories.items()]

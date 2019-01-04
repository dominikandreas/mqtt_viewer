from paho.mqtt.client import Client as MQTTClient
#import numpy as np
import json
import time
import os
import traceback
import pickle
import jinja2


ROOT = os.path.abspath(os.path.dirname(__file__))
DB_PATH = ROOT + "/data.db"
AVAILABLE_APIS = []
from apscheduler.schedulers.background import BackgroundScheduler


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
        if os.path.isfile(self.path):
            with open(self.path, "rb") as f:
                self.db = pickle.load(f)

    def save(self):
        try:
            with open(self.path+".tmp", "wb") as f:
                pickle.dump(self.db, f)
            if os.path.isfile(self.path):
                os.remove(self.path)
            os.rename(self.path+".tmp", self.path)
        except:
            traceback.print_exc()

    def __exit__(self, exc_type, exc_value, tb):
        self.scheduler.shutdown()
        del self.scheduler


class MQTTLogger:
    def __init__(self, server, graph_def, db, port=1883, history_size=600, on_view_update=None):
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

    @property
    def histories(self):
        return self.db["histories"]

    def update_resolutions(self, name, history):
        resolutions = self.resolutions
        for (res, time_diff), (source, _) in zip(resolutions[1:], resolutions[:-1]):
            source, data = history.get(source), history.get(res, [])
            if len(data) > 0:
                if source[-1][0] > data[-1][0]+time_diff*1000:
                    new_data = [s for s in source if s[0] > data[-1][0]]
                    data.append(tuple(np.mean(new_data, axis=0)))
                    history[res] = data[-self.history_size:]
                    self.on_view_update(name, res, history[res][-1])
            else:
                history[res] = [source[0]]
                self.on_view_update(name, res, history[res][-1])

    def log(self, **entries):
        for name, value in entries.items():
            history = self.histories.get(name, {})
            data = history.get("raw", [])
            data.append([time.time()*1000, value])
            history["raw"] = data[-self.history_size:]
            self.update_resolutions(name, history)
            self.histories[name] = history

    def on_message(self, client, userdata, msg):
        try:
            data_str = str(msg.payload.decode("utf-8"))
            data = json.loads(data_str.replace("nan", "'nan'"))
            for name, entry in self.graph_def.items():
                if msg.topic == entry["topic"]:
                    template = entry["template"]
                    self.log(**{name: float(data if template is None else template.render(**data))})
        except Exception as e:
            traceback.print_exc()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        for topic in self.topics:
            client.subscribe(topic)

    def get_data_view(self, resolution="second"):
        time_records = [[d[0] for d in entry[resolution]] for entry in self.histories.values()]
        t_min = np.max([recs[0] for recs in time_records])

        return [{"name": name, "data": [d for d in data[resolution] if d[0] >= t_min]}
                for name, data in self.histories.items()]


#def gauss_filter(data, weights=(0.1, 0.2, 0.4, 0.2, 0.1)):
#    x, y = zip(*data)
#    return list(zip(x, np.convolve([*y[:5][::-1], *y, *y[-5:][::-1]], weights, "same").tolist()[5:-5]))

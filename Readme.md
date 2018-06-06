# MQTT Viewer

Simple Server+WebApp for MQTT data logging and visualization of time series. Just install, configure graphs, start viewing your MQTT topics in less than 5 minutes.

Why this and not something like [Grafana](https://grafana.com/)? Grafana is huge. This is really small, simple and easy to set up.

## Configuration

Lets pretend you're cooking meat in the oven with two temperature sensors: One for the oven and one for the meat, both connected to a microcontroller sending the data to an MQTT topic ``oven_topic`` encoded in JSON, e.g. `` { 'oven_temp': 80.0, 'meat_temp':75.5} ``. To visualize this data in a graph, you could use the following:

```yaml
graphs: # Section for configuring multiple graphs
  Oven: # Name of the graph
    'Oven Temp': # Name of an element in the graph
      topic: oven_topic
      json_template: '{{ oven_temp }}' # json / jinja2 template to parse from recieved data
    'Meat Temp':
      topic: oven_topic
      json_template: '{{ meat_temp }}'
```

Optional json_templates are used with jinja2 to extract values from json encoded messages. 
Logs of different time resolutions (seconds, minutes, hours, days) are automatically created
and corresponding graphs in the frontend are updated in real time.

Here's what it could look like:
![graph](https://github.com/dominikandreas/mqtt_viewer/blob/master/graph.png?raw=true)
(ignore the lacking realism in the details of this graph for now)

Everything is kept very simple and low level. Not a lot of features, not a lot of code, not a lot of libraries. Should be relatively easy to extend for more features, prettier looks, different layouts, etc..

## Requirements
 - Python 3 (tested with 3.6)
 - MQTT Broker (tested with mosquitto)

## Installation
```bash
git clone https://github.com/dominikandreas/mqtt_viewer.git
cd mqtt_viewer
python3 -m pip install -r requirements.txt 
```
> note: for windows users it's usually just ``python`` not ``python3``, but make sure you've got the correct version

## Starting
- execute ``python3 server.py``
- follow instructions to create your ``config.yaml``
- open the displayed host address in your browser

finally, edit ``config.yaml`` to your liking and restart the server

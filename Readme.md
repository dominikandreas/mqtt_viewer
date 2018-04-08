# MQTT Viewer

Simple App for MQTT data logging and visualization.

This allows you to define graphs to be displayed based 
on MQTT topics. Here's a config example:

```yaml
graphs:
  Oven:
    'Oven Temp':
      topic: test_topic
      json_template: '{{ oven_temp }}'
    'Meat Temp':
      topic: test_topic
      json_template: '{{ meat_temp }}'
```
Optional json_templates are used with jinja2 to extract values from json encoded messages. 
Logs of different time resolutions (seconds, minutes, hours, days) are automatically created
and corresponding graphs in the frontend are updated in real time.

Here's what it could look like:
![graph](https://github.com/dominikandreas/mqtt_viewer/blob/master/graph.png?raw=true)
(ignore the lacking realism in the details of this graph for now)

Everything is kept very simple and low level. Not a lot of 
features, not a lot of code, not a lot of libraries.
Should be relatively easy to extend for more features, 
prettier looks, different layouts, etc..

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

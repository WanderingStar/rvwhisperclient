#!env python
import re
import sys
from client import SensorClient


def flatten(s):
    return re.sub("\\W+", "", s.lower())


client = SensorClient("192.168.86.99")
id = sys.argv[0].split("_", 1)[-1]
sensor = client.get_sensor(id, "PT300S")

if 'config' in sys.argv:
    print(f"graph_tile {sensor.title}")
    for s in sensor.series.values():
        if s.title == "Sensor Status":
            continue
        flat = flatten(s.title)
        print(f"{flat}.label {s.title}")
        if "(%)" in s.title:
            print(f"{flat}.min 0")
            print(f"{flat}.max 100")
    print("graph_category sensors")
else:
    for s in sensor.series.values():
        if s.title == "Sensor Status":
            continue
        flat = flatten(s.title)
        print(f"{flat}.value {s.last()}")


import argparse
import json
from datetime import datetime

import requests
from collections import OrderedDict


class Sensor:
    def __init__(self, json):
        self.json = json
        self.id = int(json['sensor_id'])
        self.title = json['sensor_title']
        if json.get('data') is not None:
            self.series = {k: SensorData(k, v) for k, v in json['data'].items()}
        if json.get('alerts') is not None:
            self.alerts = [a['title'] for a in json['alerts']]

    def __str__(self):
        return f"{self.id}: {self.title}"


class SensorData:
    _known_types = {
        'RSSI (dB)': int,
        'Sensor Status': str,
    }

    def __init__(self, title, data):
        self.title = title
        self.data = OrderedDict()
        data_type = self._known_types.get(title, float)
        for point in data:
            self.data[datetime.fromisoformat(point['x'])] = data_type(point['y'])

    def __str__(self):
        return f"{self.title}:\n" + "\n".join(f"{k.isoformat()}, {v}" for k, v in self.data.items())


class SensorClient:
    def __init__(self, host):
        self.host = host

    def list_sensors(self):
        # This URL should be /api/v1/sensors
        url = f"http://{self.host}/sensor?list=1"
        r = requests.get(url)
        return sorted([Sensor(v) for v in r.json().get('sensors').values()], key=lambda x: x.id)

    def get_sensor(self, id, interval="PT3H"):
        # This URL should be /api/v1/sensor/{id}
        url = f"http://{self.host}/sensor?json=1&sensor_id={id}&interval={interval}"
        r = requests.get(url)
        return Sensor(r.json())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='The hostname of your RV whisper')
    parser.add_argument('sensor', help='The numeric identifier of a sensor', nargs='*', type=int)
    parser.add_argument('-s', '--seconds', help='Number of seconds of history', default=3600, type=int)
    output = parser.add_mutually_exclusive_group()
    output.add_argument('-u', '--human', action='store_true', help='Output human readable')
    output.add_argument('-j', '--json', action='store_true', help='Output JSON')
    output.add_argument('-l', '--last', action='store_true', help='Output only last value')
    args = parser.parse_args()

    client = SensorClient(args.host)
    if len(args.sensor) == 0:
        sensors = client.list_sensors()
        if args.json:
            j = {s.id:s.json for s in sensors}
            print(json.dumps(j))
        else:
            for sn in sensors:
                print(sn)
    else:
        php_interval = f"PT{args.seconds}S"
        sensors = [client.get_sensor(s, php_interval) for s in args.sensor]
        if args.last:
            for s in sensors:
                print(f"{s.title}\t{s.id}")
                for r in s.series.values():
                    print(f"{r.title}\t{list(r.data.values())[-1]}")
        elif args.json:
            j = {}
            for s in sensors:
                j[s.id] = {k.title: [(t.isoformat(), v) for t,v in  k.data.items()] for k in s.series.values()}
            print(json.dumps(j, indent=2))


if __name__ == '__main__':
    main()

"""

c = SensorClient("192.168.86.99")
s = c.list_sensors()
print(s)
for sn in s:
    print(sn)

print(c.get_sensor('545').series['DC Voltage (Volts)'])

host = "192.168.86.99"
base_url = f"http://{host}/sensor"

r = requests.get(f"{base_url}?list=1")
sensors = r.json().get('sensors');

for sensor in sensors:
    s = requests.get(f"{base_url}?json=1&sensor_id={sensor}&interval=PT5M")
    json = s.json()
    title = json['sensor_title']
    data = json['data']
    for key in data:
        if len(data[key]) == 0:
            continue
        if key in ["RSSI (dB)", "Sensor Status", "Seconds Offline",
                   "Sensor Battery Level (%)", "Sensor Battery Status"]:
            continue
        points = [float(r['y']) for r in data[key]]
        arr = np.array(points)
        print(f"{title}: {key}")
        print(f"\tmax: {np.max(arr)}\tmin: {np.min(arr)}\tavg:{np.average(arr)}")

"""
import argparse
import json
import urllib.request
from collections import OrderedDict
from datetime import datetime

from tabulate import tabulate


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

    def last(self):
        return list(self.data.values())[-1]

    def __str__(self):
        return f"{self.title}:\n" + "\n".join(f"{k.isoformat()}, {v}" for k, v in self.data.items())


class SensorClient:
    def __init__(self, host):
        self.host = host

    def list_sensors(self):
        # This URL should be /api/v1/sensors
        url = f"http://{self.host}/sensor?list=1"
        with urllib.request.urlopen(url) as u:
            j = json.loads(u.read().decode('utf-8'))
            return sorted([Sensor(v) for v in j.get('sensors').values()], key=lambda x: x.id)

    def get_sensor(self, id, interval="PT3H"):
        # This URL should be /api/v1/sensor/{id}
        url = f"http://{self.host}/sensor?json=1&sensor_id={id}&interval={interval}"
        with urllib.request.urlopen(url) as u:
            return Sensor(json.loads(u.read().decode('utf-8')))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='The hostname of your RV whisper')
    parser.add_argument('sensor', help='The numeric identifier of a sensor', nargs='*', type=int)
    parser.add_argument('-s', '--seconds', help='Number of seconds of history', default=3600, type=int)
    output = parser.add_mutually_exclusive_group()
    output.add_argument('-u', '--human', action='store_true', help='Output human readable (Default)')
    output.add_argument('-j', '--json', action='store_true', help='Output JSON')
    output.add_argument('-l', '--last', action='store_true', help='Output only last value')
    args = parser.parse_args()

    client = SensorClient(args.host)
    if len(args.sensor) == 0:
        sensors = client.list_sensors()
        if args.json:
            j = {s.id: s.json for s in sensors}
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
                    print(f"{r.title}\t{r.last()}")
        elif args.json:
            j = {}
            for s in sensors:
                j[s.id] = {k.title: [(t.isoformat(), v) for t, v in k.data.items()] for k in s.series.values()}
            print(json.dumps(j, indent=2))
        else:
            for s in sensors:
                print(f"{s.title}:")
                data = []
                headers = ["Timestamp"] + list(s.series.keys())
                for e in s.series.values():
                    if data == []:
                        data = [[t.astimezone().isoformat(" ") for t in e.data.keys()]]
                    data.append(e.data.values())
                print(tabulate(zip(*data), headers))


if __name__ == '__main__':
    main()

import json
import os
from time import sleep
from sys import stdout

result = {}
connected_clients = set()


def flatten_object(obj, parent_key=''):
    items = []
    obj.url = obj['request']['host'] + obj['request']['uri']
    for key, value in obj.items():
        new_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, dict):
            flatten_object(value, new_key)
        else:
            if new_key not in result:
                result[new_key] = {}
            if isinstance(value, list):
                if len(value) == 1:
                    value = value[0]
                else:
                    value = len(value)
            if value not in result[new_key].keys():
                result[new_key][value] = 0
            result[new_key][value] += 1
    return dict(items)


def output(message):
    print(message)
    stdout.flush()


def analyse_logs(last_ts=0, start_line=0):
    lines = []
    with open('access.log', 'r') as file:
        for i in range(start_line+100):
            line = file.readline()
            if not line:
                break
            lines.append(line)

    if len(lines[-1]) == 0:
        lines = lines[:-1]

    if last_ts:
        valid_lines = []
        for line in lines:
            try:
                data = json.loads(line)
                if data['ts'] > last_ts:
                    valid_lines.append(line)
            except:
                continue
        lines = valid_lines

    if len(lines) == 0 or (len(lines) == 1 and len(lines[0]) == 0):
        sleep(1)
        return analyse_logs(last_ts, start_line)

    for line in lines:
        try:
            data = json.loads(line)

            if not line or len(line) == 0 or 'logger' not in data or data['logger'] != 'http.log.access':
                continue

            flatten_object(data)
            output(json.dumps(result))
        except Exception as e:
            print(e)
            continue

    new_save = {
        'output': result if result else {},
        'last_ts': json.loads(lines[-1])['ts'] if 'ts' in json.loads(lines[-1]) else last_ts,
        'start_line': start_line+len(lines)
    }
    with open(os.path.dirname(__file__) + '/caddylyser.save', 'w') as file:
        file.write(json.dumps(new_save))

    return analyse_logs(json.loads(lines[-1])['ts'], start_line+len(lines))


try:
    if os.path.isfile(os.path.dirname(__file__) + '/caddylyser.save'):
        with open(os.path.dirname(__file__) + '/caddylyser.save', 'r') as file:
            try:
                save = json.loads(file.read())
                result = save['output']
                restored_last_ts = save['last_ts']
                restored_start_line = save['start_line']
                analyse_logs(restored_last_ts, restored_start_line)
            except:
                analyse_logs()
    else:
        analyse_logs()
except:
    analyse_logs()

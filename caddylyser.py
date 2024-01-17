import json
import os
from time import sleep
from sys import stdout
import importlib.util

addons = []

PATH = os.path.dirname(__file__)
for file in os.listdir(os.path.join(PATH, 'addons')):
    if file.endswith('.py'):
        addon_name = file[:-3]  # remove '.py' extension
        addon_path = os.path.join(PATH, 'addons', file)
        spec = importlib.util.spec_from_file_location(addon_name, addon_path)
        addon = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(addon)
        addons.append(addon)

print('Log: Imported ' + str(len(addons)) + ' addons')

result = {}
connected_clients = set()


def flatten_object(obj, parent_key=''):
    items = []

    obj['caddylyser'] = {}
    # Remap Values
    if 'duration' in obj:
        if isinstance(obj['duration'], list):
            rounded = math.ceil(obj['duration'][0]*10)/10
        else:
            rounded = math.ceil(obj['duration']*10)/10
        obj['duration'] = rounded
    if 'ts' in obj:
        if isinstance(obj['ts'], list):
            rounded = math.ceil(obj['ts'][0])
        else:
            rounded = math.ceil(obj['ts'])
        obj['ts'] = rounded
    if 'request' in obj and 'host' in obj['request'] and 'uri' in obj['request']:
        obj['caddylyser']['url'] = obj['request']['host'] + obj['request']['uri']
    if 'request' in obj and 'headers' in obj['request'] and 'Referer' in obj['request']['headers'] and len(obj['request']['headers']['Referer']) > 0:
        obj['caddylyser']['RefererDomain'] = urlparse(obj['request']['headers']['Referer'][0]).netloc
    #     obj['caddylyser']['source'] = urlparse(obj['request']['headers']['Referer'][0]).netloc
    # else:
    #     obj['caddylyser']['source'] = 'direct'
    #     pass
    # obj['caddylyser']['source'] = urlparse(obj['request']['headers']['Referer'][0]).netloc if 'request' in obj and 'headers' in obj['request'] and 'Referer' in obj['request']['headers'] and len(obj['request']['headers']['Referer']) > 0 else 'direct'
    if 'request' in obj and 'headers' in obj['request'] and 'Accept-Language' in obj['request']['headers'] and len(obj['request']['headers']['Accept-Language']) > 0:
        obj['caddylyser']['language'] = obj['request']['headers']['Accept-Language'][0].split(',')[0].split(';')[0].split('-')[0].lower()

        # Flatten
    for key, value in obj.items():
        new_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, dict):
            if len(value) == 0:
                continue
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


def read_next_lines(file_path, start_byte, line_count):
    lines = []
    with open(file_path, 'r') as file:
        file.seek(start_byte)
        for _ in range(line_count):
            line = file.readline()
            if not line:
                break
            lines.append(line)


def analyse_logs(last_ts=0, start_line=0, read_bytes=0):
    output('Log: Reading Logs From Byte ' + str(read_bytes))

    try:
        lines = read_next_lines(os.path.dirname(__file__) + '/access.log', read_bytes, 1000)
    except:
        output('Error: Cannot read access.log')
        sleep(1)
        return analyse_logs(last_ts, start_line, read_bytes)

    output('Log: Removing empty lines')
    if len(lines) != 0 and len(lines[-1]) == 0:
        lines = lines[:-1]

    print('Log: Skipping some Logs')
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
        return analyse_logs(last_ts, start_line, read_bytes)

    for line in lines:
        i += 1
        data = {}

        found_addon = True
        for addon in addons:
            try:
                if addon.match(line):
                    found_addon = True
                    break
            except Exception as e:
                print('Error: Addon ' + addon.__name__ + ' crashed on match', e)
                pass

        if not found_addon:
            output('Error: No addon found for line')
            continue

        try:
            data = addon.handler(line)
        except Exception as e:
            print('Error: Addon ' + addon.__name__ + ' crashed on handler', e)
            data = False
        if not data:
            output('Error: Addon ' + addon.__name__ + ' failed to parse line')
            continue

        flatten_object(data)

    output(json.dumps(result))

    if os.path.isfile(os.path.dirname(__file__) + '/caddylyser.queue.save') and os.path.getsize(os.path.dirname(__file__) + '/access.log'):
        with open(os.path.dirname(__file__) + '/caddylyser.queue.save', 'r') as queue_item:
            queue_item = queue_item.read()
            if len(queue_item) and queue_item[0] == '{' and queue_item[-1] == '}':
                global last_save
                last_save = queue_item
                with open(os.path.dirname(__file__) + '/caddylyser.save', 'w') as file:
                    file.write(queue_item)

    new_save = {
        'output': result if result else {},
        'last_ts': data['ts'] if 'ts' in data else last_ts,
        'start_line': start_line+len(lines),
        'read_bytes': read_bytes
    }
    with open(os.path.dirname(__file__) + '/caddylyser.queue.save', 'w') as file:
        file.write(json.dumps(new_save))

    return analyse_logs(data['ts'], start_line+len(lines), read_bytes)


try:
    if os.path.isfile(os.path.dirname(__file__) + '/caddylyser.save'):
        with open(os.path.dirname(__file__) + '/caddylyser.save', 'r') as file:
            try:
                save = json.loads(file.read())
                result = save['output']
                output(json.dumps(result))
                restored_last_ts = save['last_ts']
                restored_start_line = save['start_line']
                restored_read_bytes = save['read_bytes']
                analyse_logs(restored_last_ts, restored_start_line, restored_read_bytes)
            except:
                analyse_logs()
    else:
        analyse_logs()
except:
    analyse_logs()

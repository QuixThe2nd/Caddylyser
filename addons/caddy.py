import json


def match(log):
    return log.startswith('{') and log.endswith('}')

def handler(log):
    data = json.loads(log)
    print(data)

    if not data or len(data) == 0 or 'logger' not in data or data['logger'] != 'http.log.access':
        return False

    return data
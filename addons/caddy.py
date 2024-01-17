import json


def match(log):
    return log.startswith('{')

def handler(log):
    data = json.loads(log)

    if not data or len(data) == 0 or 'logger' not in data or data['logger'] != 'http.log.access':
        return False

    return data
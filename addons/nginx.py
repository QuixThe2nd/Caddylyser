import re
from datetime import datetime
import time as time_module


def match(log):
    return re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", log)

def handler(log):
    regex = r"(.+) - - \[(.+)] \"([A-Z]+) (.+) (.+)\" (\d+) (\d+) \"(.+)\" \"(.*)\" \"(.+)\" \"-\""
    matches = re.finditer(regex, log)
    for matchNum, match in enumerate(matches, start=1):
        time = match.group(2).split(' ')[0]

        dt = datetime.strptime(time, '%d/%b/%Y:%H:%M:%S')
        unix_timestamp = int(time_module.mktime(dt.timetuple()))

        return {
            'status': match.group(6),
            'ts': unix_timestamp,
            'request': {
                'proto': match.group(5),
                'method': match.group(3),
                'uri': match.group(4),
                'headers': {
                    'X-Forwarded-For': match.group(10),
                    'User-Agent': match.group(9),
                    'Referer': match.group(8),
                    'Content-Length': match.group(7),
                },
                'remote_ip': match.group(1),
            }
        }
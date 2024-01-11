import json
import asyncio
import websockets

result = {}


def flatten_object(obj, parent_key=''):
    items = []
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


async def analyse_logs(last_ts=0):
    with open('access.log', 'r') as file:
        lines = file.read().split('\n')

    if len(lines[-1]) == 0:
        lines = lines[:-1]

    if last_ts:
        lines = [line for line in lines if json.loads(line)['ts'] > last_ts]

    if len(lines) == 0:
        await asyncio.sleep(1)
        return await analyse_logs(last_ts)

    i = 0
    for line in lines:
        i += 1
        if not line:
            continue

        data = json.loads(line)

        if 'logger' not in data or data['logger'] != 'http.log.access':
            continue

        flatten_object(data)

        result['backlog'] = len(lines) - i

        await send_to_clients(result)

    return await analyse_logs(json.loads(lines[-1])['ts'])

connected_clients = set()

async def send_to_clients(message):
    if connected_clients:  # Check if there are any connected clients
        await asyncio.wait([client.send(json.dumps(message)) for client in connected_clients])

async def register(websocket):
    connected_clients.add(websocket)

async def unregister(websocket):
    connected_clients.remove(websocket)

async def server(websocket, path):
    await register(websocket)
    try:
        await websocket.wait_closed()
    finally:
        await unregister(websocket)

start_server = websockets.serve(server, "localhost", 5901)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_until_complete(analyse_logs())
asyncio.get_event_loop().run_forever()

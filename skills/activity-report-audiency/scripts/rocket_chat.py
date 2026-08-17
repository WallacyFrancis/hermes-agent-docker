#!/usr/bin/env python3
"""Login and send a direct message through Rocket.Chat REST."""
import argparse, json, sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
BASE = 'https://chat.audiency.io:50010'; ROOM = 'cGmiKBd2WHaGb95yZ'; ENV = Path('/mnt/host/.env')
def env():
    values = {}
    for line in ENV.read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1); values[k.strip()] = v.strip().strip('"').strip("'")
    return values
def call(path, body, headers={}):
    req = Request(BASE + path, json.dumps(body).encode(), headers={'Content-Type':'application/json', **headers}, method='POST')
    try:
        with urlopen(req, timeout=30) as response: return json.loads(response.read())
    except HTTPError as error: raise RuntimeError(f'Rocket.Chat HTTP {error.code}: {error.read().decode(errors="replace")[:300]}')
def login():
    values = env(); email, password = values.get('ROCKETCHAT_EMAIL'), values.get('ROCKETCHAT_PASSWORD')
    if not email or not password: raise RuntimeError('ROCKETCHAT_EMAIL e ROCKETCHAT_PASSWORD não estão disponíveis em /mnt/host/.env')
    data = call('/api/v1/login', {'user': email, 'password': password}).get('data', {})
    if not data.get('authToken') or not data.get('userId'): raise RuntimeError('login do Rocket.Chat não retornou sessão válida')
    return {'X-Auth-Token': data['authToken'], 'X-User-Id': data['userId']}
def main():
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest='command', required=True); send = sub.add_parser('send'); send.add_argument('--message', required=True); args=parser.parse_args()
    result = call('/api/v1/chat.sendMessage', {'message': {'rid': ROOM, 'msg': args.message}}, login())
    if not result.get('success', False): raise RuntimeError(f'falha ao enviar mensagem: {result}')
    print('Mensagem enviada ao Rocket.Chat.')
if __name__ == '__main__':
    try: main()
    except RuntimeError as error:
        print(f'erro: {error}', file=sys.stderr); sys.exit(1)

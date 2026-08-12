import time
import requests
import json
from dotenv import load_dotenv
import os
from pathlib import Path

# Cargar API key desde .env
load_dotenv()
KEY = os.environ.get('API_KEY')
if not KEY:
    raise SystemExit("Falta API_KEY en el .env")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

BASE = 'https://api.steampowered.com/IStoreTopSellersService/GetWeeklyTopSellers/v1/'

WEEK = 604800
FIRST_TUE = 1262044800  # 2009-12-29

# Obtiene los datos semanales de una pagina
def get_week(start_ts, page=0):
    body = {
        'start_date': start_ts,
        'page_start': page * 50,
        'page_count': 50,
        'context': {'language': 'english', 'country_code': 'US'},
        'data_request': {
            'include_basic_info': True,
            'include_release': True
        },
    }

    url = f'{BASE}?key={KEY}&input_json={json.dumps(body)}'
    res = requests.get(url)
    return json.loads(res.text)['response']

# Itera la funcion get_week en varias paginas
def get_week_full(start_ts):
    ranks, page, week_start = [], 0, None
    while True:
        res = get_week(start_ts, page)
        if week_start is None:
            week_start = res.get('start_date', start_ts)
        ranks += res.get('ranks', [])
        if not res.get('next_page_start'):
            break
        page += 1
        time.sleep(1) 
    return week_start, ranks

# Obtiene datos iniciales
latest = get_week(None)['start_date']

# Itera y guarda en un checkpoint.json hasta la actualidad
games = {}
for ts in range(FIRST_TUE, latest + 1, WEEK):
    week_start, ranks = get_week_full(ts)
    for res in ranks:
        item = res['item']
        g = games.setdefault(item['appid'],{
            'name': item.get('name', ''),
            'release': item.get('release', {}).get('steam_release_date'),
            'prices': [],
            'weeks': {}
        })

        bpo = item.get('best_purchase_option', {})
        if bpo.get('original_price_in_cents'):
            g['prices'].append(int(bpo['original_price_in_cents']) / 100)
        g['weeks'][week_start] = res['rank']
    time.sleep(1.5)

    if (ts - FIRST_TUE) % (52 * WEEK) < WEEK:
        print(f'processing week {ts} ... ({len(games)} unique games)')

    if (ts - FIRST_TUE) % (26 * WEEK) == 0:
        with open(DATA / "checkpoint.json", "w") as f:
            json.dump(games, f)

# guardado final
with open(DATA / "checkpoint.json", "w") as f:
    json.dump(games, f)
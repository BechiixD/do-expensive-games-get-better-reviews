import json
import time
import requests
import os
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path

load_dotenv()
KEY = os.environ.get('API_KEY')
if not KEY:
    raise SystemExit("Falta API_KEY en el .env")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# 1) cargás tu checkpoint
games = {int(k): v for k, v in json.load(open(DATA / "checkpoint.json")).items()}
appids = list(games.keys())

# 2) enriquecés TODOS con GetItems
def get_items_batch(ids):
    body = {
        "ids": [{"appid": i} for i in ids],
        "context": {"language": "english", "country_code": "US"},
        "data_request": {
            "include_basic_info": True,
            "include_all_purchase_options": True,
            "include_release": True,
        },
    }
    r = requests.get(
        "https://api.steampowered.com/IStoreBrowseService/GetItems/v1/",
        params={"key": KEY, "input_json": json.dumps(body)},
    )
    return r.json()["response"]["store_items"]

enriched = {}
for i in range(0, len(appids), 100):
    for it in get_items_batch(appids[i:i+100]):
        enriched[it["appid"]] = it
    time.sleep(1)

# 3) helpers
def msrp_of(item, appid):
    po = item.get("purchase_options") or []
    base = next((o for o in po if o.get("package_group") == "default"), po[0] if po else None)
    if base:
        final = base.get("final_price_in_cents")
        orig = base.get("original_price_in_cents") or final
        if final is not None:
            try:
                return max(int(orig), int(final)) / 100
            except (ValueError, TypeError):
                pass
    # fallback a prices del checkpoint
    prices = [p for p in games.get(appid, {}).get("prices", []) if p > 0]
    if prices:
        return max(prices)  # más seguro que statistics.mode
    return None

def release_of(item, appid):
    ts = (item.get("release") or {}).get("steam_release_date")
    if ts: return ts
    return games.get(appid, {}).get("release")

# 4) build selected
selected = []
for appid, it in enriched.items():
    if it.get("type") not in (0, None):
        continue
    price = msrp_of(it, appid)
    if price is None or price <= 0:
        continue
    rel_ts = release_of(it, appid)
    selected.append({
        "appid": appid,
        "name": it.get("name", ""),
        "msrp": price,
        "release_ts": rel_ts,
        "n_weeks": len(games[appid]["weeks"]),
        "is_free": bool(it.get("is_free")),
    })

print(f"selected final: {len(selected)}")

# 5) GUARDAR
df = pd.DataFrame(selected)
df.to_csv(DATA / "selected.csv", index=False)
print("guardado: selected.csv")

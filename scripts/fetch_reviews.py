import pandas as pd, requests, time

from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

selected = pd.read_csv(DATA / 'selected.csv')

def get_reviews(appid):
    url = f'https://store.steampowered.com/appreviews/{appid}'
    params = {'json': 1, 'num_per_page': 0, 'language': 'all', 'purchase_type': 'all'}
    r = requests.get(url, params=params, headers={'User-Agent': 'MNozilla/5.0'}, timeout=20)
    q = r.json()['query_summary']

    return {
        'appid': appid,
        'total_positive': q.get('total_positive', 0),
        'total_negative': q.get('total_negative', 0),
        'total_reviews': q.get('total_reviews', 0),
        'review_score_desc': q.get('review_score_desc', ''),
    }

reviews = []
for appid in selected['appid']:
    try:
        reviews.append(get_reviews(appid))
        print(f'fetched n. {appid}')
    except Exception as e:
        print(f'{appid} failed: {e}')
        time.sleep(1.2)

reviews_df = pd.DataFrame(reviews)
reviews_df.to_csv(DATA / 'reviews.csv', index=False)

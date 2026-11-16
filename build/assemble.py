"""Make thumbnails, add GBIF record counts, and write ../index.html from template.html."""
import json, os, requests
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
S = requests.Session(); S.headers['User-Agent'] = "SingingFolioPrototype/0.1"
birds = json.load(open(os.path.join(HERE, 'species_assets.json')))
puzzles = json.load(open(os.path.join(HERE, 'puzzles.json')))
os.makedirs(os.path.join(ROOT, 'assets', 'thumbs'), exist_ok=True)
def map_view(path):
    """Crop window [x, y, w] (h = w/2) covering the central 98% of recorded density, padded."""
    a = Image.open(path).getchannel('A'); W, H = a.size; px = a.load()
    cols = [sum(1 for y in range(H) if px[x, y]) for x in range(W)]
    rows = [sum(1 for x in range(W) if px[x, y]) for y in range(H)]
    def span(v):
        tot = sum(v); acc = 0; lo = hi = None
        for i, c in enumerate(v):
            acc += c
            if lo is None and acc >= tot * 0.01: lo = i
            if hi is None and acc >= tot * 0.99: hi = i
        return lo or 0, hi if hi is not None else len(v) - 1
    if not any(cols): return [0, 0, W]
    x0, x1 = span(cols); y0, y1 = span(rows)
    w = max(x1 - x0, (y1 - y0) * 2, 300) * 1.25
    w = min(W, w); h = w / 2
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x = min(max(0, cx - w / 2), W - w); y = min(max(0, cy - h / 2), H - h)
    return [round(x), round(y), round(w)]
for b in birds:
    t = f"assets/thumbs/{b['plate']}.jpg"
    if not os.path.exists(os.path.join(ROOT, t)):
        im = Image.open(os.path.join(ROOT, b['img']['file'])); im.thumbnail((420, 610), Image.LANCZOS)
        im.save(os.path.join(ROOT, t), quality=78, optimize=True, progressive=True)
    b['thumb'] = t
    b['mapView'] = map_view(os.path.join(ROOT, b['map']))
    if 'records' not in b:
        try: b['records'] = int(S.get('https://api.gbif.org/v1/occurrence/count', params={'taxonKey': b['gbif']}, timeout=30).text)
        except Exception: b['records'] = None
keep = ['plate', 'common', 'latin', 'gould_common', 'gould_latin', 'order', 'family', 'gbif', 'img', 'thumb', 'map', 'mapView', 'sound', 'records']
data = [{k: b.get(k) for k in keep} for b in birds]
rounds = [{'birds': p['birds'], 'odd': p['odd'], 'pair': p['pair']} for p in puzzles]
html = open(os.path.join(HERE, 'template.html'), encoding='utf8').read()
html = html.replace('/*BIRDS*/[]', json.dumps(data, ensure_ascii=False)).replace('/*ROUNDS*/[]', json.dumps(rounds, ensure_ascii=False))
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf8').write(html)
print('wrote index.html;', sum(1 for b in birds if b['sound']), 'of', len(birds), 'birds have recordings')
for b in birds: print(f"{b['plate']:>3} {b['common']:26} {b['records']}  {(b['sound'] or {}).get('license')}")

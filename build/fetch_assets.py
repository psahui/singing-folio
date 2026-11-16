"""Download plates (Commons), recordings (iNaturalist) and occurrence maps (GBIF) for the Folio."""
import json, io, time, re, sys, os, requests
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
S = requests.Session(); S.headers['User-Agent'] = "SingingFolioPrototype/0.1 (personal non-commercial project)"
_orig = S.request
S.request = lambda *a, **k: _orig(*a, **{'timeout': 30, **k})
S.mount('https://', HTTPAdapter(max_retries=Retry(total=6, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=None)))
HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(HERE, '..', 'assets')
species = json.load(open(os.path.join(HERE, 'species_match.json')))
plates = {r['n']: r for r in json.load(open(sys.argv[1]))}   # raw_plates.json from the Commons scrape
LICS = 'cc0,cc-by,cc-by-nc,cc-by-sa,cc-by-nc-sa'

def get_plate(sp):
    r = plates[sp['plate']]
    out = os.path.join(A, 'plates', f"{sp['plate']}.jpg")
    if not os.path.exists(out):
        img = Image.open(io.BytesIO(S.get(r['url']).content)).convert('RGB')
        img.thumbnail((1000, 1450), Image.LANCZOS); img.save(out, quality=80, optimize=True, progressive=True)
        time.sleep(1)
    return dict(file=f"assets/plates/{sp['plate']}.jpg", source=f"https://commons.wikimedia.org/wiki/{r['title'].replace(' ', '_')}")

def get_sound(sp):
    for extra in ({'place_id': 6744}, {}):          # Australia first, then anywhere
        obs = S.get('https://api.inaturalist.org/v1/observations', params=dict(taxon_id=sp['inat'], sounds='true', quality_grade='research', sound_license=LICS, order_by='votes', per_page=12, **extra)).json()['results']
        time.sleep(1)
        for o in obs:
            for s in o.get('sounds', []):
                url = s.get('file_url') or ''
                ct = s.get('file_content_type') or ''
                ext = 'mp3' if 'mpeg' in ct else 'm4a' if 'mp4' in ct else None
                if not url or not ext: continue
                h = S.head(url, allow_redirects=True); size = int(h.headers.get('content-length', 0))
                if not 20_000 < size < 1_400_000: continue
                out = os.path.join(A, 'audio', f"{sp['plate']}.{ext}")
                open(out, 'wb').write(S.get(url).content)
                return dict(file=f"assets/audio/{sp['plate']}.{ext}", attribution=s.get('attribution'), license=s.get('license_code'),
                            obs=f"https://www.inaturalist.org/observations/{o['id']}", place=o.get('place_guess'), date=o.get('observed_on'))
    return None

def get_map(sp):
    out = os.path.join(A, 'maps', f"{sp['plate']}.png")
    if not os.path.exists(out):
        canvas = Image.new('RGBA', (1024, 512))
        for x in (0, 1):
            t = S.get(f"https://api.gbif.org/v2/map/occurrence/density/0/{x}/0@1x.png", params=dict(taxonKey=sp['gbif'], srs='EPSG:4326', style='classic.point'))
            if t.status_code == 200 and t.content: canvas.paste(Image.open(io.BytesIO(t.content)).convert('RGBA'), (x * 512, 0))
        canvas.save(out, optimize=True)
    return f"assets/maps/{sp['plate']}.png"

CACHE = os.path.join(HERE, 'sound_cache.json')
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
for sp in species:
    sp['img'] = get_plate(sp); sp['map'] = get_map(sp)
    key = str(sp['plate'])
    if key not in cache:
        try: cache[key] = get_sound(sp)
        except Exception as e: print('  sound failed:', e); cache[key] = None
        json.dump(cache, open(CACHE, 'w'), indent=1)
    sp['sound'] = cache[key]
    print(sp['plate'], sp['common'], '| sound:', (sp['sound'] or {}).get('license'), (sp['sound'] or {}).get('place'), flush=True)
json.dump(species, open(os.path.join(HERE, 'species_assets.json'), 'w'), indent=1)

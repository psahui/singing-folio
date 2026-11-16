"""Fetch the Open Tree of Life synthetic tree pruned to the Folio's species, and score every triplet.
For a triplet, the 'odd bird out' is the one whose common ancestor with the other two is deepest in the past,
i.e. the other two share a more recent common ancestor (fewer steps from the root)."""
import json, os, re, itertools, requests
S = requests.Session(); S.headers['User-Agent'] = "SingingFolioPrototype/0.1"
HERE = os.path.dirname(os.path.abspath(__file__))
species = json.load(open(os.path.join(HERE, 'species_match.json')))
names = [s['latin'] for s in species]
m = S.post('https://api.opentreeoflife.org/v3/tnrs/match_names', json={'names': names, 'context_name': 'Birds', 'do_approximate_matching': False}).json()
ott = {}
for r in m['results']:
    tx = r['matches'][0]['taxon'] if r['matches'] else None
    ott[r['name']] = tx['ott_id'] if tx else None
    if not tx or tx['unique_name'].lower() != r['name'].lower(): print('CHECK', r['name'], tx and tx['unique_name'])
# Taxa that are not monophyletic in the synthetic tree are 'broken': use the node the API maps them to instead.
leaf_label = {k: f"ott{v}" for k, v in ott.items() if v}
t = S.post('https://api.opentreeoflife.org/v3/tree_of_life/induced_subtree', json={'ott_ids': [v for v in ott.values() if v], 'label_format': 'id'}).json()
broken = t.get('broken') or {}
if broken:
    for k, v in leaf_label.items():
        if v in broken: leaf_label[k] = broken[v]
    ids = list(leaf_label.values())
    t = S.post('https://api.opentreeoflife.org/v3/tree_of_life/induced_subtree', json={'node_ids': ids, 'label_format': 'id'}).json()
newick = t['newick']; print('broken taxa (remapped):', broken)
# --- recursive newick parse -> ancestor paths
pos = 0
def parse():
    global pos
    kids = []
    if newick[pos] == '(':
        pos += 1
        while True:
            kids.append(parse())
            if newick[pos] == ',': pos += 1; continue
            if newick[pos] == ')': pos += 1; break
    m = re.match(r"[^(),;:]*", newick[pos:]); label = m.group(0); pos += len(label)
    if pos < len(newick) and newick[pos] == ':':
        m2 = re.match(r":[^(),;]*", newick[pos:]); pos += len(m2.group(0))
    return {'label': label, 'kids': kids}
tree = parse()
paths = {}
def walk(n, path):
    p = path + [id(n)]
    paths[n['label']] = p
    for k in n['kids']: walk(k, p)
walk(tree, [])
by_latin = {}
for latin, key in leaf_label.items():
    o = key
    if key in paths: by_latin[latin] = paths[key]
    else: print('MISSING in tree', latin, o)
def depth(a, b):   # length of shared ancestor path = how recent their common ancestor is
    pa, pb = by_latin[a], by_latin[b]; n = 0
    for x, y in zip(pa, pb):
        if x != y: break
        n += 1
    return n
lat = list(by_latin)
pair_depth = {f"{a}|{b}": depth(a, b) for a in lat for b in lat if a < b}
triplets = []
for a, b, c in itertools.combinations(lat, 3):
    d = {'ab': depth(a, b), 'ac': depth(a, c), 'bc': depth(b, c)}
    best = max(d.values())
    if list(d.values()).count(best) > 1: continue          # unresolved: no clear odd one
    pair = max(d, key=d.get)
    odd = {'ab': c, 'ac': b, 'bc': a}[pair]
    triplets.append({'birds': [a, b, c], 'odd': odd})
json.dump({'source': 'Open Tree of Life synthetic tree v3 API, induced subtree', 'ott': ott, 'newick': newick, 'pair_depth': pair_depth, 'n_triplets': len(triplets)}, open(os.path.join(HERE, 'tree.json'), 'w'), indent=1)
print(len(triplets), 'resolved triplets of', len(list(itertools.combinations(lat, 3))))
def show(a, b, c):
    for t in triplets:
        if set(t['birds']) == {a, b, c}: return t['odd']
    return 'unresolved'
for trio in [("Falco peregrinus","Aquila audax","Cacatua galerita"),("Podargus strigoides","Ninox boobook","Dacelo novaeguineae"),
             ("Eudyptula minor","Diomedea exulans","Cygnus atratus"),("Menura novaehollandiae","Ptilonorhynchus violaceus","Malurus cyaneus"),
             ("Ardenna tenuirostris","Diomedea exulans","Limosa lapponica"),("Gymnorhina tibicen","Cracticus nigrogularis","Manorina melanocephala"),
             ("Merops ornatus","Dacelo novaeguineae","Melopsittacus undulatus"),("Pelecanus conspicillatus","Eudyptula minor","Vanellus miles")]:
    print(trio, '->', show(*trio))
print(newick[:600])

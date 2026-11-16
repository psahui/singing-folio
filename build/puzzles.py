"""Curated Odd Bird Out rounds. Answers come from tree.json (Open Tree of Life); clade names from the OTL mrca API."""
import json, os, requests
S = requests.Session(); S.headers['User-Agent'] = "SingingFolioPrototype/0.1"
HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(HERE, 'tree.json')))
pd = T['pair_depth']
def d(a, b): return pd[f"{min(a,b)}|{max(a,b)}"]
ROUNDS = [  # chosen because appearance points the wrong way, or the answer is a good story
 ("Falco peregrinus", "Aquila audax", "Cacatua galerita"),
 ("Podargus strigoides", "Ninox boobook", "Dacelo novaeguineae"),
 ("Eudyptula minor", "Diomedea exulans", "Cygnus atratus"),
 ("Pelecanus conspicillatus", "Eudyptula minor", "Vanellus miles"),
 ("Gymnorhina tibicen", "Cracticus nigrogularis", "Manorina melanocephala"),
 ("Menura novaehollandiae", "Ptilonorhynchus violaceus", "Malurus cyaneus"),
 ("Ardenna tenuirostris", "Diomedea exulans", "Limosa lapponica"),
 ("Merops ornatus", "Dacelo novaeguineae", "Melopsittacus undulatus"),
 ("Falco peregrinus", "Melopsittacus undulatus", "Ninox boobook"),
 ("Cygnus atratus", "Pelecanus conspicillatus", "Vanellus miles"),
]
ott = T['ott']
out = []
for trio in ROUNDS:
    pairs = [(trio[0], trio[1], trio[2]), (trio[0], trio[2], trio[1]), (trio[1], trio[2], trio[0])]
    a, b, odd = max(pairs, key=lambda p: d(p[0], p[1]))
    r = S.post('https://api.opentreeoflife.org/v3/tree_of_life/mrca', json={'ott_ids': [ott[a], ott[b]]}).json()
    clade = (r.get('nearest_taxon') or {}).get('name')
    r2 = S.post('https://api.opentreeoflife.org/v3/tree_of_life/mrca', json={'ott_ids': [ott[a], ott[b], ott[odd]]}).json()
    clade_all = (r2.get('nearest_taxon') or {}).get('name')
    out.append({'birds': list(trio), 'odd': odd, 'pair': [a, b], 'pair_clade': clade, 'all_clade': clade_all})
    print(trio, '-> odd:', odd, '| pair in:', clade, '| all three in:', clade_all)
json.dump(out, open(os.path.join(HERE, 'puzzles.json'), 'w'), indent=1)

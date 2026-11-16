# The Singing Folio

A small, non-commercial educational site that pairs John Gould's 19th-century plates from *The Birds of Australia* with real field recordings of each bird. As a recording plays, a live spectrogram draws the song, and a GBIF map shows where the species has been recorded. It also includes **Odd Bird Out**, a ten-round quiz on which birds are actually related, based on the Open Tree of Life.

Open `index.html` in a browser, or serve the folder locally. For example:

```bash
python -m http.server 8765
```

## What's in it

- 27 species, 26 with recordings. iNaturalist has no openly licensed recording of the Wandering Albatross, so it has none.
- A live spectrogram (Web Audio API), and a plate that glows with the volume of the recording.
- A GBIF occurrence-density map for each species, cropped to its range.
- Odd Bird Out: 10 curated rounds. Every answer comes from the Open Tree of Life synthetic tree, and the explanations use GBIF order and family.

## Rebuilding

The scripts in `build/` regenerate everything from public APIs.

| Script | What it does |
|---|---|
| `species.py` | The species roster: Gould plate number, Gould's names, modern names |
| `fetch_assets.py` | Downloads plates (Wikimedia Commons), recordings (iNaturalist) and density maps (GBIF) |
| `tree.py` | Fetches the induced subtree from the Open Tree of Life |
| `puzzles.py` | Defines and checks the Odd Bird Out rounds |
| `assemble.py` | Makes thumbnails, adds record counts, and writes `index.html` from `template.html` |

The scripts need Python 3 with `requests` and `Pillow`.

## Sources and licences

- **Plates:** John Gould, *The Birds of Australia* (1840–48). The scans are by rawpixel via Wikimedia Commons, under CC BY-SA 4.0.
- **Recordings:** iNaturalist contributors. Each recording's licence (CC BY or CC BY-NC) and recordist are credited on its page in the site. Because most are CC BY-NC, **this project must remain non-commercial**.
- **Maps and taxonomy:** [GBIF](https://www.gbif.org). Map tiles are derived from GBIF occurrence data and the GBIF basemap (OpenMapTiles / OpenStreetMap contributors).
- **Relatedness:** [Open Tree of Life](https://tree.opentreeoflife.org) synthetic tree.

The compiler matched Gould's historical names to modern species. These matches have not been independently verified.

Media files keep their original licences. Nothing in this repository relicenses them.

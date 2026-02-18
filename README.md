# Bangor Dining Health Tracker

Interactive map + scraper for Maine health inspection data in Bangor.

## What this project does
- Scrapes Bangor inspection records from Maine's public inspection search portal.
- Generates `inspections.json` with establishment metadata and map coordinates.
- Serves a Leaflet map (`index.html`) that displays restaurants with status coloring.

## Files
- `scraper.py`: Main scraper (writes `inspections.json` and `scraper.log`).
- `inspection_scraper.py`: Older alternate scraper script.
- `index.html`: Map UI.
- `inspections.json`: Generated data consumed by the map.
- `scraper.log`: Run/debug log.
- `requirements.txt`: Python dependencies.

## Setup
```bash
cd /Users/DMacleod/sandbox/projects/inspections-scraper/temp-repo
python3 -m pip install -r requirements.txt
```

## Run scraper
```bash
cd /Users/DMacleod/sandbox/projects/inspections-scraper/temp-repo
python3 scraper.py
```

Expected output includes:
- `DEBUG: Found ... potential rows.`
- `Success: ... establishments saved.`

## Run map locally
Do not open `index.html` directly from `file://`.
Use a local server:

```bash
cd /Users/DMacleod/sandbox/projects/inspections-scraper/temp-repo
python3 -m http.server 8020
```

Then open:
- `http://localhost:8020/index.html`

## Troubleshooting
### `OSError: [Errno 48] Address already in use`
Port is occupied. Use another port:
```bash
python3 -m http.server 8030
```
Or free the port:
```bash
lsof -nP -iTCP:8020 -sTCP:LISTEN
kill <PID>
```

### `Error code: 404 File not found`
You started the server from the wrong directory or opened wrong URL path.

Verify:
```bash
pwd
ls -l index.html inspections.json
```

### Map says `Data failed to load: Failed to fetch`
Usually caused by opening via `file://` or wrong server directory.
Run through `python3 -m http.server` in this folder.

### Some points look wrong
Coordinates come from geocoding and can fail for malformed addresses.
Check `scraper.log` for:
- `geocode_error`
- `skipped_no_geocode`

## Data notes
- Current scraper processes up to 50 rows (`rows = rows[:50]`).
- Geocoding is rate-limited to avoid hammering external services.

## Next improvement ideas
- Add deterministic coordinate cache to reduce repeat geocoding.
- Parse and normalize addresses before geocoding.
- Add a "no geocode" fallback list for known venues.

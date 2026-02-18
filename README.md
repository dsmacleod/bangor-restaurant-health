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

## Data notes
- Current scraper processes up to 50 rows (`rows = rows[:50]`).
- Geocoding is rate-limited to avoid hammering external services.

## Next improvement ideas
- Add deterministic coordinate cache to reduce repeat geocoding.
- Parse and normalize addresses before geocoding.
- Add a "no geocode" fallback list for known venues.

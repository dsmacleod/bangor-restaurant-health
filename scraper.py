import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError, GeocoderTimedOut

# Use a specific User-Agent to look like a real Chrome browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Content-Type': 'application/x-www-form-urlencoded',
}

geolocator = Nominatim(user_agent="bangor_health_map_2026")

def get_color(status_raw):
    status = status_raw.lower()
    # Maine usually reports "Passed: X Critical, Y Non-Critical"
    if "failed" in status: return "red"
    if "critical" in status:
        # Extract number before "Critical"
        try:
            critical_count = int(status.split("critical")[0].strip().split()[-1])
            if critical_count >= 3: return "red"
            if critical_count >= 1: return "yellow"
        except: pass
    return "green"

def run_health_scraper():
    print("DEBUG: starting scraper")
    session = requests.Session()
    url = "https://apps.web.maine.gov/online/hip_search/health-inspection-search.html"
    base_dir = Path(__file__).resolve().parent
    log_path = base_dir / "scraper.log"
    data_path = base_dir / "inspections.json"
    geocode_cache = {}
    
    try:
        # prepare log file
        log_file = open(log_path, 'a')
        log_file.write('starting run\n')
        # Step 1: Visit the page first to get the session cookie and CSRF token
        resp0 = session.get(url, headers=HEADERS)
        soup0 = BeautifulSoup(resp0.text, 'html.parser')
        csrf_token = None
        token_input = soup0.find('input', {'name': '_csrf'})
        if token_input:
            csrf_token = token_input.get('value')
        
        # Step 2: Submit the search for 'Bangor' including the CSRF token
        payload = {'city': 'Bangor', 'submit': 'Search'}
        if csrf_token:
            payload['_csrf'] = csrf_token
        response = session.post(url, data=payload, headers=HEADERS, timeout=30)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Find all table rows
        rows = soup.find_all('tr')[1:]  # Skip header
        print(f"DEBUG: Found {len(rows)} potential rows.")
        log_file.write(f'rows={len(rows)}\n')
        # during development limit the number of entries so we don't wait minutes
        rows = rows[:50]

        for row in rows:  # process every row
            cols = row.find_all('td')
            if len(cols) >= 4:
                # column 0 holds name, address and county separated by <br>
                parts = [s.strip() for s in cols[0].stripped_strings]
                name = parts[0] if parts else ''
                addr_short = parts[1] if len(parts) > 1 else ''
                addr_full = f"{addr_short}, Bangor, ME" if addr_short else 'Bangor, ME'
                date = cols[2].get_text(strip=True)
                status = cols[3].get_text(strip=True)

                lat = None
                lon = None
                if addr_full in geocode_cache:
                    lat, lon = geocode_cache[addr_full]
                else:
                    try:
                        location = geolocator.geocode(addr_full, timeout=10)
                        if location:
                            lat = location.latitude
                            lon = location.longitude
                            geocode_cache[addr_full] = (lat, lon)
                        time.sleep(1.0)  # Respect Nominatim rate limits.
                    except (GeocoderTimedOut, GeocoderServiceError) as geocode_err:
                        log_file.write(f'geocode_error address="{addr_full}" error="{geocode_err}"\n')
                        time.sleep(1.0)

                if lat is None or lon is None:
                    # Skip entries without valid coordinates so bad markers don't appear on the map.
                    log_file.write(f'skipped_no_geocode name="{name}" address="{addr_full}"\n')
                    continue

                results.append({
                    "name": name,
                    "date": date,
                    "lat": lat,
                    "lng": lon,
                    "color": get_color(status),
                    "details": status,
                    "address": addr_full
                })

        # Final data structure
        final_data = {
            "last_run": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "establishments": results
        }

        with open(data_path, 'w') as f:
            json.dump(final_data, f, indent=2)
        print(f"Success: {len(results)} establishments saved.")
        log_file.write(f'success count={len(results)}\n')
        log_file.close()

    except Exception as e:
        print(f"Error: {e}")
        try:
            with open(log_path, 'a') as log_file:
                log_file.write(f'error: {e}\n')
        except:
            pass

if __name__ == "__main__":
    run_health_scraper()

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
from geopy.geocoders import Nominatim

# Use a specific User-Agent to look like a real Chrome browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Content-Type': 'application/x-www-form-urlencoded',
}

geolocator = Nominatim(user_agent="bangor_health_map_2026_v2")

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
    session = requests.Session()
    url = "https://apps.web.maine.gov/online/hip_search/health-inspection-search.html"
    
    try:
        # Step 1: Visit the page first to get the Session Cookie
        session.get(url, headers=HEADERS)
        
        # Step 2: Submit the search for 'Bangor'
        payload = {'city': 'Bangor', 'submit': 'Search'}
        response = session.post(url, data=payload, headers=HEADERS, timeout=30)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Find all table rows
        rows = soup.find_all('tr')[1:] # Skip header
        print(f"DEBUG: Found {len(rows)} potential rows.")

        for row in rows[:20]: # Limit to 20 for testing
            cols = row.find_all('td')
            if len(cols) >= 4:
                name = cols[0].get_text(strip=True)
                addr_short = cols[1].get_text(strip=True)
                addr_full = f"{addr_short}, Bangor, ME"
                date = cols[2].get_text(strip=True)
                status = cols[3].get_text(strip=True)
                
                # Geocode
                try:
                    location = geolocator.geocode(addr_full)
                    if location:
                        lat, lon = location.latitude, location.longitude
                    else:
                        # Fail-safe: Downtown Bangor + tiny random offset so pins don't stack
                        lat = 44.8016 + (random.uniform(-0.01, 0.01))
                        lon = -68.7712 + (random.uniform(-0.01, 0.01))
                        
                    results.append({
                        "name": name,
                        "date": date,
                        "lat": lat,
                        "lng": lon,
                        "color": get_color(status),
                        "details": status,
                        "address": addr_full
                    })
                    time.sleep(1.2) # Essential for GeoPy free tier
                except:
                    continue

        # Final data structure
        final_data = {
            "last_run": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "establishments": results
        }

        with open('inspections.json', 'w') as f:
            json.dump(final_data, f, indent=2)
            
        print(f"Success: {len(results)} establishments saved.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_health_scraper()

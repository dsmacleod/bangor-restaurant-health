import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from geopy.geocoders import Nominatim

# 1. Stealth Setup
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Origin': 'https://apps.web.maine.gov',
    'Referer': 'https://apps.web.maine.gov/online/hip_search/health-inspection-search.html'
}

geolocator = Nominatim(user_agent="bangor_health_tracker_2026")

def get_color(status_text):
    """Categorizes the status string from the Maine portal into colors."""
    status = status_text.lower()
    if "failed" in status or "critical" in status and any(x in status for x in ["3", "4", "5"]):
        return "red"
    elif "critical" in status and any(x in status for x in ["1", "2"]):
        return "yellow"
    return "green"

def run_health_scraper():
    search_url = "https://apps.web.maine.gov/online/hip_search/health-inspection-search.html"
    
    # These keys match the hidden technical names in the Maine portal's form
    payload = {
        'establishmentName': '',
        'city': 'Bangor',
        'submit': 'Search'
    }
    
    try:
        # Step 1: Submit the search form
        response = requests.post(search_url, data=payload, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Step 2: Find the results table
        # We look for the table containing 'Establishment' or 'Inspection Date'
        results = []
        rows = soup.find_all('tr')[1:] # Skip the header row
        
        if not rows:
            print("No rows found. The portal might be rate-limiting or the city name is unrecognized.")
            return

        for row in rows[:25]: # Process the most recent 25 entries
            cols = row.find_all('td')
            if len(cols) >= 5:
                name = cols[0].get_text(strip=True)
                addr = f"{cols[1].get_text(strip=True)}, Bangor, ME"
                date = cols[2].get_text(strip=True)
                # Status column usually contains both the 'Passed/Failed' and the counts
                status_raw = cols[3].get_text(strip=True) 
                
                # Geocode to get Map coordinates
                try:
                    location = geolocator.geocode(addr)
                    if location:
                        results.append({
                            "name": name,
                            "date": date,
                            "lat": location.latitude,
                            "lng": location.longitude,
                            "color": get_color(status_raw),
                            "details": status_raw,
                            "address": addr
                        })
                    time.sleep(1.1) # Respect the free geocoder's rate limit
                except Exception as e:
                    print(f"Skipping {name} due to geocoding error: {e}")

        # Save results with a timestamp
        output = {
            "last_run": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "establishments": results
        }

        with open('inspections.json', 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Successfully scraped {len(results)} establishments.")
            
    except Exception as e:
        print(f"Fatal Scraper Error: {e}")

if __name__ == "__main__":
    run_health_scraper()

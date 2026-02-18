import requests
from bs4 import BeautifulSoup
import json
import time
from geopy.geocoders import Nominatim
from datetime import datetime
from pathlib import Path

geolocator = Nominatim(user_agent="bangor_health_map")

def get_inspection_color(status, critical, non_critical):
    if status.lower() == "failed" or int(critical) >= 3:
        return "red"
    elif int(critical) > 0 or int(non_critical) > 5:
        return "yellow"
    return "green"

def scrape_bangor_health():
    base_dir = Path(__file__).resolve().parent
    data_path = base_dir / "inspections.json"
    # Maine portal search URL
    search_url = "https://apps.web.maine.gov/online/hip_search/health-inspection-search.html"
    
    # fetch CSRF token first
    resp0 = requests.get(search_url)
    soup0 = BeautifulSoup(resp0.text, 'html.parser')
    csrf_token = None
    token_input = soup0.find('input', {'name': '_csrf'})
    if token_input:
        csrf_token = token_input.get('value')

    # We simulate a POST request to search by 'Bangor'
    payload = {
        'establishmentName': '',
        'city': 'Bangor',
        'submit': 'Search'
    }
    if csrf_token:
        payload['_csrf'] = csrf_token
    
    response = requests.post(search_url, data=payload)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = []
    # Find the results table (adjust selectors based on specific page HTML)
    rows = soup.find_all('tr')[1:] # Skip header
    
    for row in rows[:20]: # Limit to 20 for example
        cols = row.find_all('td')
        if len(cols) > 5:
            name = cols[0].text.strip()
            address = f"{cols[1].text.strip()}, Bangor, ME"
            status = cols[3].text.strip()
            c_violations = cols[4].text.strip() or 0
            nc_violations = cols[5].text.strip() or 0
            
            color = get_inspection_color(status, c_violations, nc_violations)
            
            # Geocode the address
            try:
                location = geolocator.geocode(address)
                if location:
                    results.append({
                        "name": name,
                        "address": address,
                        "lat": location.latitude,
                        "lng": location.longitude,
                        "status": status,
                        "critical": c_violations,
                        "non_critical": nc_violations,
                        "color": color
                    })
                time.sleep(1) # Respect geocoding limits
            except:
                continue

    # wrap results in object with timestamp so the front-end can display a date
    final_data = {
        "last_run": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        "establishments": results
    }
    with open(data_path, 'w') as f:
        json.dump(final_data, f, indent=2)

if __name__ == "__main__":
    scrape_bangor_health()

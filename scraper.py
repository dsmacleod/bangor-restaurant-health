import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from geopy.geocoders import Nominatim

# Initialize Geocoder
geolocator = Nominatim(user_agent="bangor_health_map_2026")

def get_color(status, critical):
    try:
        critical_count = int(critical)
    except:
        critical_count = 0
    if status.lower() == "failed" or critical_count >= 3:
        return "red"
    elif critical_count > 0:
        return "yellow"
    return "green"

def run_health_scraper():
    url = "https://apps.web.maine.gov/online/hip_search/health-inspection-search.html"
    payload = {'city': 'Bangor', 'submit': 'Search'}
    
    try:
        response = requests.post(url, data=payload, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        rows = soup.find_all('tr')[1:] # Skip header
        
        for row in rows[:30]: # Grab top 30 recent results
            cols = row.find_all('td')
            if len(cols) >= 6:
                name = cols[0].text.strip()
                addr = f"{cols[1].text.strip()}, Bangor, ME"
                # Extracting Date from the search result table
                inspect_date = cols[3].text.strip() 
                status = cols[4].text.strip()
                critical = cols[5].text.strip() or "0"
                
                location = geolocator.geocode(addr)
                if location:
                    results.append({
                        "name": name,
                        "date": inspect_date,
                        "lat": location.latitude,
                        "lng": location.longitude,
                        "color": get_color(status, critical),
                        "details": f"Status: {status} | Critical: {critical}",
                        "address": addr
                    })
                time.sleep(1) # Be nice to the geocoder

        # Add a global "last updated" time for the map header
        data_packet = {
            "last_run": datetime.now().strftime("%B %d, %Y at %H:%M"),
            "establishments": results
        }

        with open('inspections.json', 'w') as f:
            json.dump(data_packet, f)
            
    except Exception as e:
        print(f"Scraper failed: {e}")

if __name__ == "__main__":
    run_health_scraper()

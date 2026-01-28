import requests
from bs4 import BeautifulSoup
import json
import time
from geopy.geocoders import Nominatim

# Initialize Geocoder
geolocator = Nominatim(user_agent="bangor_health_map_2026")

def get_color(status, critical):
    """Logic for 🟢 Green, 🟡 Yellow, 🔴 Red markers"""
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
    # Maine Health Inspection Portal
    url = "https://apps.web.maine.gov/online/hip_search/health-inspection-search.html"
    
    # Simulate searching for 'Bangor'
    payload = {'city': 'Bangor', 'submit': 'Search'}
    
    try:
        response = requests.post(url, data=payload, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        rows = soup.find_all('tr')[1:] # Skip the table header
        
        for row in rows[:25]: # Grab the latest 25 inspections
            cols = row.find_all('td')
            if len(cols) >= 5:
                name = cols[0].text.strip()
                addr = f"{cols[1].text.strip()}, Bangor, ME"
                status = cols[3].text.strip()
                critical = cols[4].text.strip() or "0"
                
                # Geocode address to Map Coordinates
                location = geolocator.geocode(addr)
                if location:
                    results.append({
                        "name": name,
                        "lat": location.latitude,
                        "lng": location.longitude,
                        "color": get_color(status, critical),
                        "details": f"Status: {status} | Critical: {critical}"
                    })
                time.sleep(1) # Respect geocoding rate limits

        with open('inspections.json', 'w') as f:
            json.dump(results, f)
            
    except Exception as e:
        print(f"Scraper failed: {e}")

if __name__ == "__main__":
    run_health_scraper()

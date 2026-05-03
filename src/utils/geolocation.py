import requests
from datetime import datetime

def get_client_ip(request):
    """Extract client IP from request, handling proxies"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr or '0.0.0.0'

def get_location_from_ip(ip_address):
    """Get location data from IP address using ip-api.com"""
    if ip_address in ['127.0.0.1', 'localhost', '0.0.0.0']:
        return {
            'country': 'Local',
            'region': 'Local',
            'city': 'Local',
            'lat': 0.0,
            'lon': 0.0
        }

    try:
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}',
            timeout=3
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'country': data.get('country', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'lat': data.get('lat', 0.0),
                    'lon': data.get('lon', 0.0)
                }
    except Exception as e:
        print(f"[WARNING] Geolocation lookup failed: {e}")

    return {
        'country': 'Unknown',
        'region': 'Unknown',
        'city': 'Unknown',
        'lat': 0.0,
        'lon': 0.0
    }

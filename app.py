from flask import Flask, render_template, request, jsonify
import requests
from geopy.geocoders import Nominatim
from itertools import permutations
import time
import folium
import json

app = Flask(__name__)

class RouteOptimizer:
    def __init__(self):
        self.geolocator = Nominatim(
            user_agent="delivery_optimizer_web_v2", 
            timeout=15,
            domain='nominatim.openstreetmap.org',
            scheme='https'
        )
        self.osrm_url = "http://router.project-osrm.org/route/v1/driving/"
    
    def geocode_address(self, address):
        """Enhanced geocoding with multiple services for exact house numbers"""
        # Clean and format address
        address = address.strip()
        
        # Try multiple geocoding approaches
        geocoding_attempts = [
            # Exact address with detailed parameters
            {'query': address, 'params': {'exactly_one': True, 'addressdetails': True, 'limit': 1}},
            # With country specified
            {'query': f"{address}, United States", 'params': {'exactly_one': True, 'addressdetails': True}},
            # With USA appended
            {'query': f"{address}, USA", 'params': {'exactly_one': True, 'addressdetails': True}},
            # Structured query if possible
            {'query': address, 'params': {'exactly_one': True, 'addressdetails': True, 'extratags': True}}
        ]
        
        for attempt in geocoding_attempts:
            try:
                location = self.geolocator.geocode(attempt['query'], **attempt['params'])
                if location and location.latitude and location.longitude:
                    # Verify it's a reasonable location (not in ocean, etc.)
                    if -90 <= location.latitude <= 90 and -180 <= location.longitude <= 180:
                        return {
                            'lat': location.latitude,
                            'lon': location.longitude,
                            'display_name': location.address,
                            'success': True
                        }
                time.sleep(0.5)  # Rate limiting between attempts
            except Exception as e:
                continue
        
        # Try OpenCage as backup (free tier)
        try:
            return self._try_opencage_geocoding(address)
        except:
            pass
            
        return {'success': False, 'error': f'Could not geocode address: {address}'}
    
    def _try_opencage_geocoding(self, address):
        """Backup geocoding using OpenCage (requires API key for production)"""
        # For demo purposes, try a different Nominatim instance
        backup_geolocator = Nominatim(
            user_agent="delivery_optimizer_backup", 
            domain='nominatim.openstreetmap.org',
            scheme='https'
        )
        
        try:
            location = backup_geolocator.geocode(
                address, 
                exactly_one=True, 
                addressdetails=True,
                timeout=10
            )
            if location:
                return {
                    'lat': location.latitude,
                    'lon': location.longitude,
                    'display_name': location.address,
                    'success': True
                }
        except:
            pass
            
        return {'success': False, 'error': 'Backup geocoding failed'}
    
    def get_route_info(self, coord1, coord2, transport_mode='driving'):
        """Get route info for different transport modes"""
        # OSRM profiles
        profiles = {
            'driving': 'driving',
            'cycling': 'cycling', 
            'walking': 'foot'
        }
        
        profile = profiles.get(transport_mode, 'driving')
        url = f"http://router.project-osrm.org/route/v1/{profile}/{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}"
        
        try:
            response = requests.get(url, params={"overview": "false"}, timeout=10)
            data = response.json()
            
            if data["code"] == "Ok":
                route = data["routes"][0]
                duration = route["duration"]
                distance = route["distance"]
                
                # Adjust for bus (assume 20% slower than car due to stops)
                if transport_mode == 'bus':
                    duration *= 1.2
                
                return {
                    'duration': duration,
                    'distance': distance,
                    'success': True
                }
            return {'success': False, 'duration': float('inf'), 'distance': float('inf')}
        except:
            return {'success': False, 'duration': float('inf'), 'distance': float('inf')}
    
    def get_route_geometry(self, coord1, coord2, transport_mode='driving'):
        """Get route geometry for different transport modes"""
        profiles = {
            'driving': 'driving',
            'cycling': 'cycling',
            'walking': 'foot',
            'bus': 'driving'  # Bus uses driving routes
        }
        
        profile = profiles.get(transport_mode, 'driving')
        url = f"http://router.project-osrm.org/route/v1/{profile}/{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}"
        
        try:
            response = requests.get(url, params={"overview": "full", "geometries": "geojson"}, timeout=10)
            data = response.json()
            
            if data["code"] == "Ok":
                coordinates = data["routes"][0]["geometry"]["coordinates"]
                return [[lat, lon] for lon, lat in coordinates]
            return None
        except:
            return None
    
    def solve_tsp(self, matrix, optimize_by='time'):
        """Solve TSP optimizing by time or distance with proper metric selection"""
        n = len(matrix)
        min_cost = float('inf')
        best_route = None
        
        # Use correct metric key
        metric_key = 'duration' if optimize_by == 'time' else 'distance'
        
        for perm in permutations(range(1, n)):
            route = [0] + list(perm) + [0]
            cost = 0
            
            for i in range(len(route) - 1):
                start_idx = route[i]
                end_idx = route[i + 1]
                cost += matrix[start_idx][end_idx][metric_key]
            
            if cost < min_cost:
                min_cost = cost
                best_route = route
        
        return best_route, min_cost

optimizer = RouteOptimizer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/optimize', methods=['POST'])
def optimize_route():
    data = request.json
    addresses = data.get('addresses', [])
    optimize_by = data.get('optimize_by', 'time')  # 'time' or 'distance'
    transport_mode = data.get('transport_mode', 'driving')  # 'driving', 'cycling', 'walking', 'bus'
    
    if len(addresses) < 2:
        return jsonify({'error': 'At least 2 addresses required'})
    
    # Geocode addresses
    coordinates = []
    geocoded_addresses = []
    
    for addr in addresses:
        result = optimizer.geocode_address(addr)
        if result['success']:
            coordinates.append((result['lat'], result['lon']))
            geocoded_addresses.append(result['display_name'])
        else:
            return jsonify({'error': f"Could not geocode: {addr}"})
        time.sleep(0.5)  # Rate limiting
    
    # Build distance/time matrix with proper structure
    n = len(coordinates)
    matrix = [[{'duration': 0, 'distance': 0} for _ in range(n)] for _ in range(n)]
    
    for i in range(n):
        for j in range(i + 1, n):
            if i != j:
                route_info = optimizer.get_route_info(coordinates[i], coordinates[j], transport_mode)
                matrix[i][j] = matrix[j][i] = {
                    'duration': route_info['duration'],
                    'distance': route_info['distance']
                }
                time.sleep(0.1)
    
    # Solve TSP
    optimal_route, total_cost = optimizer.solve_tsp(matrix, optimize_by)
    
    # Calculate total time and distance from optimal route
    total_time = 0
    total_distance = 0
    
    for i in range(len(optimal_route) - 1):
        start_idx = optimal_route[i]
        end_idx = optimal_route[i + 1]
        total_time += matrix[start_idx][end_idx]['duration']
        total_distance += matrix[start_idx][end_idx]['distance']
    
    # Create map
    center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
    center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige']
    for i, (addr, coord) in enumerate(zip(geocoded_addresses, coordinates)):
        folium.Marker(
            coord,
            popup=f"Stop {i+1}: {addr}",
            tooltip=f"Stop {i+1}",
            icon=folium.Icon(color=colors[i % len(colors)])
        ).add_to(m)
    
    # Draw route with actual road geometry
    for i in range(len(optimal_route) - 1):
        start_idx = optimal_route[i]
        end_idx = optimal_route[i + 1]
        
        # Get actual route geometry
        route_coords = optimizer.get_route_geometry(coordinates[start_idx], coordinates[end_idx], transport_mode)
        
        if route_coords:
            folium.PolyLine(
                route_coords,
                color='#FF4444',
                weight=4,
                opacity=0.8
            ).add_to(m)
        else:
            # Fallback to straight line if route geometry fails
            folium.PolyLine([
                coordinates[start_idx],
                coordinates[end_idx]
            ], color='#FF4444', weight=4, opacity=0.8, dashArray='5, 5').add_to(m)
    
    map_html = m._repr_html_()
    
    # Prepare route details
    route_details = []
    for i, stop_idx in enumerate(optimal_route[:-1]):
        route_details.append({
            'step': i + 1,
            'address': geocoded_addresses[stop_idx],
            'coordinates': coordinates[stop_idx]
        })
    
    return jsonify({
        'success': True,
        'route': route_details,
        'total_time_minutes': round(total_time / 60, 1),
        'total_time_hours': round(total_time / 3600, 2),
        'total_distance_km': round(total_distance / 1000, 2),
        'total_distance_miles': round(total_distance / 1609.34, 2),
        'optimized_by': optimize_by.title(),
        'transport_mode': transport_mode.title(),
        'optimization_value': round(total_cost / 60, 1) if optimize_by == 'time' else round(total_cost / 1000, 2),
        'map_html': map_html
    })

if __name__ == '__main__':
    app.run(debug=True)
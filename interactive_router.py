#!/usr/bin/env python3
"""
Interactive Delivery Routing System
Enter addresses and get optimal route with visualization
"""

import requests
import folium
from geopy.geocoders import Nominatim
from itertools import permutations
import time

def geocode_address(address):
    """Convert single address to coordinates"""
    geolocator = Nominatim(user_agent="delivery_router")
    try:
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        return None
    except:
        return None

def get_travel_time(coord1, coord2):
    """Get travel time between coordinates using OSRM"""
    url = f"http://router.project-osrm.org/route/v1/driving/{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}"
    try:
        response = requests.get(url, params={"overview": "false"}, timeout=10)
        data = response.json()
        return data["routes"][0]["duration"] if data["code"] == "Ok" else float('inf')
    except:
        return float('inf')

def solve_tsp(distance_matrix):
    """Solve TSP using brute force"""
    n = len(distance_matrix)
    min_cost = float('inf')
    best_route = None
    
    for perm in permutations(range(1, n)):
        route = [0] + list(perm) + [0]
        cost = sum(distance_matrix[route[i]][route[i+1]] for i in range(len(route)-1))
        if cost < min_cost:
            min_cost = cost
            best_route = route
    
    return best_route, min_cost

def create_map(addresses, coordinates, route):
    """Create interactive map"""
    center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
    center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred']
    for i, (addr, coord) in enumerate(zip(addresses, coordinates)):
        folium.Marker(
            coord, 
            popup=f"Stop {i+1}: {addr}",
            icon=folium.Icon(color=colors[i % len(colors)])
        ).add_to(m)
    
    # Draw route
    for i in range(len(route) - 1):
        folium.PolyLine([
            coordinates[route[i]], 
            coordinates[route[i+1]]
        ], color='red', weight=3).add_to(m)
    
    return m

def main():
    print("🚚 DELIVERY ROUTE OPTIMIZER")
    print("=" * 40)
    
    # Get addresses
    addresses = []
    print("Enter delivery addresses (empty line to finish):")
    
    while len(addresses) < 8:
        addr = input(f"Address {len(addresses) + 1}: ").strip()
        if not addr:
            if len(addresses) >= 2:
                break
            print("Need at least 2 addresses!")
            continue
        addresses.append(addr)
    
    print(f"\n📍 Processing {len(addresses)} addresses...")
    
    # Geocode
    coordinates = []
    for i, addr in enumerate(addresses):
        print(f"Geocoding {i+1}/{len(addresses)}: {addr}")
        coord = geocode_address(addr)
        if coord:
            coordinates.append(coord)
            print(f"✓ Found: {coord[0]:.4f}, {coord[1]:.4f}")
        else:
            print(f"✗ Failed to geocode: {addr}")
            return
        time.sleep(1)
    
    # Build distance matrix
    print("\n🗺️  Calculating distances...")
    n = len(coordinates)
    matrix = [[0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(i + 1, n):
            travel_time = get_travel_time(coordinates[i], coordinates[j])
            matrix[i][j] = matrix[j][i] = travel_time
            print(f"Distance {i+1}-{j+1}: {travel_time/60:.1f} min")
            time.sleep(0.1)
    
    # Solve TSP
    print("\n🧮 Finding optimal route...")
    route, total_time = solve_tsp(matrix)
    
    # Results
    print("\n🎯 OPTIMAL ROUTE:")
    print("-" * 30)
    for i, stop in enumerate(route[:-1]):
        print(f"{i+1}. {addresses[stop]}")
    
    print(f"\n⏱️  Total time: {total_time/60:.1f} minutes")
    print(f"⏱️  Total time: {total_time/3600:.2f} hours")
    
    # Create map
    print("\n🗺️  Creating map...")
    map_viz = create_map(addresses, coordinates, route)
    map_viz.save("delivery_route.html")
    print("✅ Map saved as 'delivery_route.html'")
    print("Open in browser to view!")

if __name__ == "__main__":
    main()
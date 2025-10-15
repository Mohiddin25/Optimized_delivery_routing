#!/usr/bin/env python3
"""
Optimized Delivery Routing System
Solves TSP using real-world addresses with geocoding and routing APIs
"""

import requests
import folium
from geopy.geocoders import Nominatim
from itertools import permutations
import time

class DeliveryRouter:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="delivery_router")
        self.osrm_base_url = "http://router.project-osrm.org/route/v1/driving/"
        
    def geocode_addresses(self, addresses):
        """Convert addresses to coordinates using Nominatim"""
        coordinates = []
        print("Geocoding addresses...")
        
        for addr in addresses:
            try:
                location = self.geolocator.geocode(addr)
                if location:
                    coordinates.append((location.latitude, location.longitude))
                    print(f"✓ {addr} -> ({location.latitude:.4f}, {location.longitude:.4f})")
                else:
                    print(f"✗ Could not geocode: {addr}")
                    return None
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"✗ Error geocoding {addr}: {e}")
                return None
                
        return coordinates
    
    def get_travel_time(self, coord1, coord2):
        """Get travel time between two coordinates using OSRM"""
        url = f"{self.osrm_base_url}{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}"
        params = {"overview": "false", "steps": "false"}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data["code"] == "Ok":
                return data["routes"][0]["duration"]  # seconds
            else:
                print(f"OSRM error: {data.get('message', 'Unknown error')}")
                return float('inf')
        except Exception as e:
            print(f"Error getting travel time: {e}")
            return float('inf')
    
    def build_distance_matrix(self, coordinates):
        """Build matrix of travel times between all points"""
        n = len(coordinates)
        matrix = [[0] * n for _ in range(n)]
        
        print("Building distance matrix...")
        for i in range(n):
            for j in range(i + 1, n):
                travel_time = self.get_travel_time(coordinates[i], coordinates[j])
                matrix[i][j] = matrix[j][i] = travel_time
                print(f"Distance {i}-{j}: {travel_time:.1f}s")
                time.sleep(0.1)  # Rate limiting
                
        return matrix
    
    def solve_tsp_brute_force(self, distance_matrix, start_index=0):
        """Solve TSP using brute force for guaranteed optimal solution"""
        n = len(distance_matrix)
        if n > 8:
            print("Warning: Brute force may be slow for >8 locations")
        
        # Generate all possible routes (excluding start point)
        other_points = [i for i in range(n) if i != start_index]
        min_cost = float('inf')
        best_route = None
        
        print("Solving TSP...")
        for perm in permutations(other_points):
            route = [start_index] + list(perm) + [start_index]
            cost = sum(distance_matrix[route[i]][route[i+1]] for i in range(len(route)-1))
            
            if cost < min_cost:
                min_cost = cost
                best_route = route
        
        return best_route, min_cost
    
    def get_route_coordinates(self, coord1, coord2):
        """Get detailed route coordinates between two points"""
        url = f"{self.osrm_base_url}{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}"
        params = {"overview": "full", "geometries": "geojson"}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data["code"] == "Ok":
                return data["routes"][0]["geometry"]["coordinates"]
            return []
        except:
            return []
    
    def visualize_route(self, addresses, coordinates, optimal_route):
        """Create interactive map visualization"""
        # Calculate map center
        center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
        center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
        
        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        # Add markers for each stop
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige']
        for i, (addr, coord) in enumerate(zip(addresses, coordinates)):
            color = colors[i % len(colors)]
            folium.Marker(
                coord,
                popup=f"Stop {i+1}: {addr}",
                tooltip=f"Stop {i+1}",
                icon=folium.Icon(color=color)
            ).add_to(m)
        
        # Draw route lines
        for i in range(len(optimal_route) - 1):
            start_idx = optimal_route[i]
            end_idx = optimal_route[i + 1]
            
            route_coords = self.get_route_coordinates(
                coordinates[start_idx], 
                coordinates[end_idx]
            )
            
            if route_coords:
                # Convert lon,lat to lat,lon for folium
                folium_coords = [[lat, lon] for lon, lat in route_coords]
                folium.PolyLine(
                    folium_coords,
                    color='red',
                    weight=3,
                    opacity=0.8
                ).add_to(m)
            else:
                # Fallback to straight line
                folium.PolyLine([
                    coordinates[start_idx],
                    coordinates[end_idx]
                ], color='red', weight=3, opacity=0.8).add_to(m)
        
        return m

def get_addresses_from_user():
    """Get delivery addresses from user input"""
    print("Enter delivery addresses (press Enter twice when done):")
    addresses = []
    
    while True:
        addr = input(f"Address {len(addresses) + 1}: ").strip()
        if not addr:
            if len(addresses) >= 2:
                break
            else:
                print("Please enter at least 2 addresses")
                continue
        addresses.append(addr)
        
        if len(addresses) >= 8:
            print("Maximum 8 addresses supported for optimal performance")
            break
    
    return addresses

def main():
    print("=" * 50)
    print("OPTIMIZED DELIVERY ROUTING SYSTEM")
    print("=" * 50)
    
    # Get addresses from user
    addresses = get_addresses_from_user()
    
    router = DeliveryRouter()
    
    # Step 1: Geocode addresses
    coordinates = router.geocode_addresses(addresses)
    if not coordinates:
        print("Failed to geocode all addresses")
        return
    
    # Step 2: Build distance matrix
    distance_matrix = router.build_distance_matrix(coordinates)
    
    # Step 3: Solve TSP
    optimal_route, total_time = router.solve_tsp_brute_force(distance_matrix)
    
    # Step 4: Display results
    print("\n" + "="*50)
    print("OPTIMAL DELIVERY ROUTE")
    print("="*50)
    print(f"Visiting {len(addresses)} locations:")
    print("-" * 30)
    
    for i, stop_idx in enumerate(optimal_route):
        if i < len(optimal_route) - 1:  # Don't repeat start address
            print(f"{i+1}. {addresses[stop_idx]}")
    
    print(f"\nTotal travel time: {total_time/60:.1f} minutes")
    print(f"Total travel time: {total_time/3600:.2f} hours")
    
    # Step 5: Create visualization
    print("\nGenerating map visualization...")
    map_viz = router.visualize_route(addresses, coordinates, optimal_route)
    map_filename = "optimal_delivery_route.html"
    map_viz.save(map_filename)
    print(f"Map saved as: {map_filename}")
    print("Open this file in your web browser to view the interactive map!")

if __name__ == "__main__":
    main()
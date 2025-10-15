#!/usr/bin/env python3
"""
Debug script to test optimization accuracy
"""

import requests
from geopy.geocoders import Nominatim
from itertools import permutations
import time

def get_route_info(coord1, coord2):
    url = f"http://router.project-osrm.org/route/v1/driving/{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}"
    try:
        response = requests.get(url, params={"overview": "false"}, timeout=10)
        data = response.json()
        if data["code"] == "Ok":
            route = data["routes"][0]
            return {
                'duration': route["duration"],
                'distance': route["distance"]
            }
    except:
        pass
    return {'duration': float('inf'), 'distance': float('inf')}

def test_optimization():
    # Test with 3 NYC locations
    coordinates = [
        (40.7589, -73.9851),  # Times Square
        (40.7829, -73.9654),  # Central Park
        (40.7062, -73.9970)   # Brooklyn Bridge
    ]
    
    names = ["Times Square", "Central Park", "Brooklyn Bridge"]
    
    print("Testing Route Optimization")
    print("=" * 40)
    
    # Build matrix
    n = len(coordinates)
    matrix = [[{'duration': 0, 'distance': 0} for _ in range(n)] for _ in range(n)]
    
    for i in range(n):
        for j in range(i + 1, n):
            if i != j:
                info = get_route_info(coordinates[i], coordinates[j])
                matrix[i][j] = matrix[j][i] = info
                print(f"{names[i]} -> {names[j]}: {info['duration']/60:.1f}min, {info['distance']/1000:.1f}km")
                time.sleep(0.5)
    
    # Test both optimizations
    for optimize_by in ['time', 'distance']:
        print(f"\nOptimizing by {optimize_by}:")
        print("-" * 20)
        
        metric_key = 'duration' if optimize_by == 'time' else 'distance'
        min_cost = float('inf')
        best_route = None
        
        for perm in permutations(range(1, n)):
            route = [0] + list(perm) + [0]
            cost = sum(matrix[route[i]][route[i+1]][metric_key] for i in range(len(route)-1))
            
            route_names = [names[i] for i in route[:-1]]
            cost_display = f"{cost/60:.1f}min" if optimize_by == 'time' else f"{cost/1000:.1f}km"
            print(f"Route: {' -> '.join(route_names)} = {cost_display}")
            
            if cost < min_cost:
                min_cost = cost
                best_route = route
        
        best_names = [names[i] for i in best_route[:-1]]
        best_display = f"{min_cost/60:.1f}min" if optimize_by == 'time' else f"{min_cost/1000:.1f}km"
        print(f"BEST: {' -> '.join(best_names)} = {best_display}")

if __name__ == "__main__":
    test_optimization()
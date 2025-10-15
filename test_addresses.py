#!/usr/bin/env python3
"""
Test script to verify exact house number geocoding
"""

from geopy.geocoders import Nominatim
import time

def test_geocoding():
    geolocator = Nominatim(
        user_agent="address_test_v1", 
        timeout=15,
        domain='nominatim.openstreetmap.org',
        scheme='https'
    )
    
    # Test addresses with exact house numbers
    test_addresses = [
        "123 Main Street, New York, NY 10001",
        "456 Oak Avenue, Brooklyn, NY 11201", 
        "789 Pine Street, Chicago, IL 60601",
        "321 Elm Drive, Los Angeles, CA 90210",
        "654 Maple Lane, Miami, FL 33101"
    ]
    
    print("Testing exact house number geocoding:")
    print("=" * 50)
    
    for addr in test_addresses:
        print(f"\nTesting: {addr}")
        try:
            location = geolocator.geocode(
                addr, 
                exactly_one=True, 
                addressdetails=True,
                timeout=10
            )
            
            if location:
                print(f"✅ SUCCESS: {location.latitude:.6f}, {location.longitude:.6f}")
                print(f"   Found: {location.address}")
            else:
                print("❌ FAILED: Address not found")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            
        time.sleep(1)  # Rate limiting

if __name__ == "__main__":
    test_geocoding()
#!/usr/bin/env python
import requests
import json

def test_services_api():
    """Test the services API endpoint"""
    url = "http://127.0.0.1:8000/api/services/"
    
    try:
        # Test without authentication first
        print("=== Testing Services API ===")
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Type: {type(data)}")
            print(f"Response Content: {json.dumps(data, indent=2)}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

def test_abonnements_api():
    """Test the abonnements API endpoint"""
    url = "http://127.0.0.1:8000/api/abonnements/"
    
    try:
        print("\n=== Testing Abonnements API ===")
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Type: {type(data)}")
            print(f"Response Content: {json.dumps(data, indent=2)}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_services_api()
    test_abonnements_api()

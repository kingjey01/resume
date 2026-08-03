#!/usr/bin/env python
import requests
import json

def test_services_with_auth():
    """Test services endpoint with authentication"""
    
    # First login to get token
    login_url = "http://127.0.0.1:8000/api/auth/login/"
    login_data = {
        "email": "jeyyeta01@gmail.com",  # Use existing user
        "password": "password123"
    }
    
    try:
        print("=== Login Test ===")
        login_response = requests.post(login_url, json=login_data)
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            tokens = login_response.json()
            access_token = tokens.get('access')
            print(f"Access token obtained: {access_token[:50]}...")
            
            # Test services endpoint with token
            services_url = "http://127.0.0.1:8000/api/services/"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            print("\n=== Services API Test ===")
            services_response = requests.get(services_url, headers=headers)
            print(f"Services Status: {services_response.status_code}")
            print(f"Services Headers: {dict(services_response.headers)}")
            print(f"Services Raw Response: {services_response.text}")
            if services_response.status_code == 200:
                try:
                    json_data = services_response.json()
                    print(f"Services Response Type: {type(json_data)}")
                    print(f"Services Count: {len(json_data)}")
                    print(f"Services Data: {json_data}")
                except Exception as e:
                    print(f"JSON Parse Error: {e}")
            else:
                print(f"Error Response: {services_response.text}")
                
            # Test abonnements endpoint
            abonnements_url = "http://127.0.0.1:8000/api/abonnements/"
            
            print("\n=== Abonnements API Test ===")
            abonnements_response = requests.get(abonnements_url, headers=headers)
            print(f"Abonnements Status: {abonnements_response.status_code}")
            
            if abonnements_response.status_code == 200:
                abonnements_data = abonnements_response.json()
                print(f"Abonnements Response Type: {type(abonnements_data)}")
                print(f"Abonnements Count: {len(abonnements_data) if isinstance(abonnements_data, list) else 'Not a list'}")
                print(f"Abonnements Data: {json.dumps(abonnements_data, indent=2)}")
            else:
                print(f"Abonnements Error: {abonnements_response.text}")
        else:
            print(f"Login failed: {login_response.text}")
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_services_with_auth()

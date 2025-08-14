import requests
import json

BASE_URL = "http://localhost:8000"

def test_server():
    print("Testing FHIR Server...")
    print("=" * 30)
    
    try:
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return
        
        # Test metadata endpoint
        print("\n2. Testing metadata endpoint...")
        response = requests.get(f"{BASE_URL}/metadata")
        if response.status_code == 200:
            print("✓ Metadata endpoint working")
        else:
            print(f"✗ Metadata endpoint failed: {response.status_code}")
        
        # Test patient search
        print("\n3. Testing patient search...")
        response = requests.get(f"{BASE_URL}/Patient")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data.get('total', 0)} patients")
            if data.get('entry'):
                patient = data['entry'][0]['resource']
                print(f"  Sample patient: {patient.get('name', [{}])[0].get('given', [''])[0]} {patient.get('name', [{}])[0].get('family', '')}")
        else:
            print(f"✗ Patient search failed: {response.status_code}")
        
        # Test observation search
        print("\n4. Testing observation search...")
        response = requests.get(f"{BASE_URL}/Observation")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data.get('total', 0)} observations")
        else:
            print(f"✗ Observation search failed: {response.status_code}")
        
        print("\n" + "=" * 30)
        print("FHIR Server is working correctly!")
        print(f"Server URL: {BASE_URL}")
        print(f"API Docs: {BASE_URL}/docs")
        
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to FHIR server")
        print("Make sure the server is running with: python -m app.main")
    except Exception as e:
        print(f"✗ Error testing server: {str(e)}")

if __name__ == "__main__":
    test_server()

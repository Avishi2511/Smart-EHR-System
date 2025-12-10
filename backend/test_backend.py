"""
Test script for Smart EHR Backend
This script tests the basic functionality of the backend system.
Usage:
    python test_backend.py
"""
import asyncio
import httpx
from datetime import datetime
BASE_URL = "http://localhost:8001"
async def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
async def test_create_patient():
    """Test patient creation"""
    print("\n=== Testing Patient Creation ===")
    
    patient_data = {
        "fhir_id": "test-patient-001",
        "nfc_card_id": "nfc-card-001",
        "first_name": "John",
        "last_name": "Doe",
        "gender": "male",
        "date_of_birth": "1960-01-15T00:00:00"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/patients/",
            json=patient_data
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            patient = response.json()
            print(f"Created patient: {patient['id']}")
            print(f"Name: {patient['first_name']} {patient['last_name']}")
            return patient['id']
        else:
            print(f"Error: {response.text}")
            return None
async def test_get_patient(patient_id):
    """Test getting patient details"""
    print("\n=== Testing Get Patient ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/patients/{patient_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            patient = response.json()
            print(f"Patient: {patient['first_name']} {patient['last_name']}")
            print(f"FHIR ID: {patient['fhir_id']}")
            print(f"Total files: {patient['total_files']}")
            print(f"Total parameters: {patient['total_parameters']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
async def test_available_models():
    """Test getting available models"""
    print("\n=== Testing Available Models ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/models/available")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Available models: {data['count']}")
            for model in data['models']:
                print(f"\nModel: {model['name']} (v{model['version']})")
                print(f"Required parameters: {', '.join(model['required_parameters'])}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
async def test_vector_db_stats():
    """Test vector database statistics"""
    print("\n=== Testing Vector DB Stats ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/queries/vector-db/stats")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"Vector DB Status: {stats['status']}")
            print(f"Total vectors: {stats['vector_database']['total_vectors']}")
            print(f"Patients: {stats['vector_database']['patients']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
async def test_manual_parameter(patient_id):
    """Test adding manual parameter"""
    print("\n=== Testing Manual Parameter ===")
    
    # Add some test parameters
    parameters = [
        {"name": "age", "value": 65.0},
        {"name": "mmse", "value": 24.0},
        {"name": "bmi", "value": 27.5},
        {"name": "glucose", "value": 110.0}
    ]
    
    async with httpx.AsyncClient() as client:
        for param in parameters:
            # Note: This endpoint doesn't exist yet, but we can add parameters via model execution
            print(f"Parameter: {param['name']} = {param['value']}")
    
    return True
async def test_model_execution(patient_id):
    """Test model execution"""
    print("\n=== Testing Model Execution ===")
    
    # Provide override parameters for testing
    request_data = {
        "patient_id": patient_id,
        "model_name": "diabetes_risk",
        "override_parameters": {
            "age": 65.0,
            "bmi": 27.5,
            "glucose": 110.0,
            "hba1c": 6.2,
            "systolic_bp": 135.0,
            "family_history_diabetes": 1.0
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/models/execute",
            json=request_data
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nModel: {result['model_name']}")
            print(f"Result ID: {result['result_id']}")
            
            if 'results' in result:
                res = result['results']
                if 'risk_score' in res:
                    print(f"Risk Score: {res['risk_score']}")
                    print(f"Risk Level: {res['risk_level']}")
                    print(f"Risk Percentage: {res['risk_percentage']}%")
                
                if 'recommendations' in res:
                    print("\nRecommendations:")
                    for rec in res['recommendations']:
                        print(f"  - {rec}")
            
            if result.get('missing_parameters'):
                print(f"\nMissing parameters: {result['missing_parameters']}")
            
            return result['result_id']
        else:
            print(f"Error: {response.text}")
            return None
async def test_get_model_results(patient_id):
    """Test getting model results"""
    print("\n=== Testing Get Model Results ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/models/results/patient/{patient_id}"
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"Total results: {len(results)}")
            
            for result in results[:3]:  # Show first 3
                print(f"\nModel: {result['model_name']}")
                print(f"Executed: {result['executed_at']}")
                if 'output_results' in result:
                    output = result['output_results']
                    if 'risk_level' in output:
                        print(f"Risk Level: {output['risk_level']}")
            
            return True
        else:
            print(f"Error: {response.text}")
            return False
async def main():
    """Run all tests"""
    print("=" * 60)
    print("Smart EHR Backend Test Suite")
    print("=" * 60)
    
    try:
        # Test health check
        if not await test_health_check():
            print("\n❌ Health check failed. Is the server running?")
            return
        
        print("\n✓ Health check passed")
        
        # Test available models
        await test_available_models()
        
        # Test vector DB stats
        await test_vector_db_stats()
        
        # Test patient creation
        patient_id = await test_create_patient()
        
        if patient_id:
            print(f"\n✓ Patient created: {patient_id}")
            
            # Test get patient
            await test_get_patient(patient_id)
            
            # Test model execution
            result_id = await test_model_execution(patient_id)
            
            if result_id:
                print(f"\n✓ Model executed: {result_id}")
                
                # Test get results
                await test_get_model_results(patient_id)
        
        print("\n" + "=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
if __name__ == "__main__":
    asyncio.run(main())

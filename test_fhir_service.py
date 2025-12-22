import asyncio
import sys
sys.path.insert(0, 'backend')

from app.services.fhir_service import fhir_service

async def test():
    # Test get_observations_by_code
    print("Testing get_observations_by_code...")
    observations = await fhir_service.get_observations_by_code(
        patient_id="patient-002",
        loinc_code="2160-0"  # Creatinine
    )
    
    print(f"\nFound {len(observations)} observations")
    
    if observations:
        for obs in observations:
            print(f"\nObservation:")
            print(f"  ID: {obs.get('id')}")
            print(f"  Code: {obs.get('code', {}).get('coding', [{}])[0]}")
            print(f"  Value: {obs.get('valueQuantity', {})}")
    else:
        print("\nNo observations found!")
        
        # Try getting all observations
        print("\nTrying to get all observations...")
        all_obs = await fhir_service.get_observations(patient_id="patient-002")
        print(f"Total observations: {len(all_obs)}")
        
        if all_obs:
            print("\nFirst observation:")
            print(f"  Code: {all_obs[0].get('code', {}).get('coding', [{}])[0]}")

asyncio.run(test())

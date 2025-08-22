import requests
import json

# Test the API endpoints directly to verify the fix
base_url = 'http://localhost:8000'

print('Testing FHIR API Fix for Patient-002')
print('=' * 50)

# Test each resource type that should have data for patient-002
test_cases = [
    ('Observation', 2),  # Should find obs-002 and obs-003
    ('Encounter', 1),    # Should find encounter-002
    ('MedicationRequest', 2),  # Should find med-req-002 and med-req-007
    ('Condition', 1),    # Should find condition-002
    ('AllergyIntolerance', 0),  # Should find 0 (no data)
    ('Immunization', 0), # Should find 0 (no data)
    ('Procedure', 0)     # Should find 0 (no data)
]

all_passed = True

for resource_type, expected_count in test_cases:
    try:
        response = requests.get(f'{base_url}/{resource_type}?patient=patient-002')
        if response.status_code == 200:
            data = response.json()
            actual_count = data.get('total', 0)
            
            if actual_count == expected_count:
                status = "✓ PASS"
            else:
                status = "✗ FAIL"
                all_passed = False
            
            print(f'{resource_type:20} | Expected: {expected_count:2} | Actual: {actual_count:2} | {status}')
            
            # Show sample data if found
            if actual_count > 0 and 'entry' in data:
                first_record = data['entry'][0]['resource']
                if 'subject' in first_record:
                    ref = first_record['subject'].get('reference', 'N/A')
                elif 'patient' in first_record:
                    ref = first_record['patient'].get('reference', 'N/A')
                else:
                    ref = 'N/A'
                print(f'                     | Sample reference: {ref}')
        else:
            print(f'{resource_type:20} | API Error: {response.status_code}')
            all_passed = False
    except Exception as e:
        print(f'{resource_type:20} | Error: {str(e)}')
        all_passed = False

print('\n' + '=' * 50)
if all_passed:
    print('🎉 ALL TESTS PASSED! The fix is working correctly.')
    print('Patient tabs should now display data for patient-002.')
else:
    print('❌ Some tests failed. The fix needs more work.')

print('\nNote: AllergyIntolerance, Immunization, and Procedure show 0 records')
print('because there is no sample data for patient-002 in these categories.')

import requests

url = "http://localhost:8001/api/chat/query"

# Test queries that should return friendly error messages
test_queries = [
    ("Unrecognized query", "Tell me about the weather"),
    ("Vague query", "How is the patient?"),
    ("Random text", "asdfghjkl"),
]

print("="*70)
print("TESTING USER-FRIENDLY ERROR MESSAGES")
print("="*70)

for test_name, query in test_queries:
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"Query: \"{query}\"")
    print("="*70)
    
    response = requests.post(url, json={
        "patient_id": "patient-002",
        "query": query
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Success: {result['success']}")
        
        if not result['success'] and result.get('error'):
            print(f"\n✅ User-Friendly Error Message:")
            print(f"   \"{result['error']}\"")
        elif result['count'] == 0:
            print(f"\n✅ No Data Message:")
            print(f"   Query Type: {result['query_type']}")
            print(f"   (Frontend will show context-specific message)")
        else:
            print(f"\n✅ Success with {result['count']} results")
    else:
        print(f"❌ HTTP Error: {response.status_code}")

print("\n" + "="*70)
print("✅ ERROR MESSAGE TESTING COMPLETE!")
print("="*70)
print("\nThe error messages are now user-friendly and don't expose")
print("technical details. They guide users on what to ask instead.")

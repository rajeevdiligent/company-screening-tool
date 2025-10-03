#!/usr/bin/env python3
"""
Test API Gateway with a simple response to verify integration
"""

import json
import requests

def test_simple_api():
    """Test the API Gateway endpoint with a simple request"""
    
    api_url = "https://6kwwwts1z6.execute-api.us-east-1.amazonaws.com/prod/search"
    
    # Test with a simple payload
    test_payload = {
        "company_name": "Test Company"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"🚀 Testing API Gateway endpoint: {api_url}")
    print(f"📤 Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        response = requests.post(
            api_url,
            json=test_payload,
            headers=headers,
            timeout=30  # Shorter timeout for testing
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        print(f"📄 Response: {response.text[:500]}...")  # First 500 chars
        
        if response.status_code == 200:
            print("✅ API Gateway integration working!")
        elif response.status_code == 504:
            print("⏰ Function is running but taking too long (timeout)")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    test_simple_api()

#!/usr/bin/env python3
"""
Simple test script to verify API Gateway integration
"""

import json
import requests
import time

def test_api_gateway():
    """Test the API Gateway endpoint"""
    
    api_url = "https://6kwwwts1z6.execute-api.us-east-1.amazonaws.com/prod/search"
    
    # Test data
    test_payload = {
        "company_name": "Apple"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"🚀 Testing API Gateway endpoint: {api_url}")
    print(f"📤 Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            api_url,
            json=test_payload,
            headers=headers,
            timeout=180
        )
        end_time = time.time()
        
        print(f"⏱️ Response time: {end_time - start_time:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Success!")
            result = response.json()
            print(f"📄 Response preview:")
            print(f"  Company: {result.get('company_name', 'N/A')}")
            print(f"  Legal Name: {result.get('legal_name', 'N/A')}")
            print(f"  Stock Symbol: {result.get('stock_symbol', 'N/A')}")
            print(f"  Executives: {len(result.get('key_executives', []))} found")
            print(f"  SEC Filings: {len(result.get('regulatory_filings', []))} found")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 180 seconds")
    except requests.exceptions.RequestException as e:
        print(f"🚨 Request failed: {e}")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")

if __name__ == "__main__":
    test_api_gateway()

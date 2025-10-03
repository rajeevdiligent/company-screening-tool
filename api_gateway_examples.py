#!/usr/bin/env python3
"""
Examples of how to get full JSON output from API Gateway
"""

import json
import requests
import time
import boto3
from datetime import datetime

# API Gateway endpoint
API_ENDPOINT = "https://6kwwwts1z6.execute-api.us-east-1.amazonaws.com/prod/search"

def method_1_direct_lambda_invoke():
    """
    Method 1: Direct Lambda invocation (bypasses API Gateway timeout)
    This gives you the full JSON output immediately
    """
    print("🚀 Method 1: Direct Lambda Invocation")
    print("=" * 50)
    
    # Initialize AWS Lambda client with session
    session = boto3.Session(profile_name='diligent')
    lambda_client = session.client('lambda', region_name='us-east-1')
    
    # Prepare payload
    payload = {
        "company_name": "Microsoft"
    }
    
    print(f"📤 Invoking Lambda directly for: {payload['company_name']}")
    start_time = time.time()
    
    try:
        # Invoke Lambda function directly
        response = lambda_client.invoke(
            FunctionName='company-screening-tool',
            InvocationType='RequestResponse',  # Synchronous
            Payload=json.dumps(payload)
        )
        
        end_time = time.time()
        print(f"⏱️ Execution time: {end_time - start_time:.2f} seconds")
        
        # Parse response
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            # Parse the body if it's a string
            if isinstance(result.get('body'), str):
                company_data = json.loads(result['body'])
            else:
                company_data = result
            
            print("✅ Success! Full JSON received:")
            print(f"  Company: {company_data.get('company_name')}")
            print(f"  Legal Name: {company_data.get('legal_name')}")
            print(f"  Stock Symbol: {company_data.get('stock_symbol')}")
            print(f"  Executives: {len(company_data.get('key_executives', []))} found")
            print(f"  SEC Filings: {len(company_data.get('regulatory_filings', []))} found")
            
            # Save to file
            output_file = f"api_output_{payload['company_name'].replace(' ', '_')}.json"
            with open(output_file, 'w') as f:
                json.dump(company_data, f, indent=2, default=str)
            print(f"💾 Saved to: {output_file}")
            
            return company_data
        else:
            print(f"❌ Error: {result}")
            return None
            
    except Exception as e:
        print(f"💥 Error: {e}")
        return None

def method_2_api_gateway_with_polling():
    """
    Method 2: API Gateway with CloudWatch Logs polling
    Start the request via API Gateway, then poll logs for completion
    """
    print("\n🚀 Method 2: API Gateway + Log Polling")
    print("=" * 50)
    
    payload = {
        "company_name": "Apple"
    }
    
    print(f"📤 Starting API Gateway request for: {payload['company_name']}")
    
    try:
        # Start the API Gateway request (will timeout, but Lambda continues)
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 API Gateway Status: {response.status_code}")
        
        if response.status_code == 504:
            print("⏰ API Gateway timed out (expected)")
            print("🔍 Lambda function is still running...")
            print("📋 You can check CloudWatch logs for completion")
            print("💡 Or use Method 1 for immediate results")
        
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (expected)")
        print("🔍 Lambda function is still running in the background")

def method_3_test_api_gateway_simple():
    """
    Method 3: Test API Gateway with a simple company name
    Some companies might be faster to process
    """
    print("\n🚀 Method 3: API Gateway Simple Test")
    print("=" * 50)
    
    # Try with a simpler company that might be faster
    payload = {
        "company_name": "Tesla"
    }
    
    print(f"📤 Testing API Gateway with: {payload['company_name']}")
    
    try:
        start_time = time.time()
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=35  # Slightly longer timeout
        )
        end_time = time.time()
        
        print(f"⏱️ Response time: {end_time - start_time:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success! API Gateway returned full results")
            result = response.json()
            print(f"  Company: {result.get('company_name')}")
            print(f"  Executives: {len(result.get('key_executives', []))} found")
            return result
        elif response.status_code == 504:
            print("⏰ Timed out - use Method 1 for full results")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
    except Exception as e:
        print(f"💥 Error: {e}")

def create_curl_examples():
    """
    Method 4: Create curl command examples
    """
    print("\n🚀 Method 4: cURL Examples")
    print("=" * 50)
    
    print("📋 Direct Lambda invocation (AWS CLI):")
    print("""
aws lambda invoke \\
  --function-name company-screening-tool \\
  --payload '{"company_name": "Microsoft"}' \\
  --profile diligent \\
  microsoft_output.json

# Then read the result:
cat microsoft_output.json | jq '.'
""")
    
    print("📋 API Gateway cURL (will timeout but Lambda continues):")
    print(f"""
curl -X POST "{API_ENDPOINT}" \\
  -H "Content-Type: application/json" \\
  -d '{{"company_name": "Microsoft"}}' \\
  --max-time 30
""")

def main():
    """Run all examples"""
    print("🎯 API Gateway JSON Output Examples")
    print("=" * 60)
    print("Goal: Get the same comprehensive JSON as lambda_search_Microsoft.json")
    print()
    
    # Method 1: Direct Lambda (recommended for full results)
    result = method_1_direct_lambda_invoke()
    
    # Method 2: API Gateway with understanding of timeout
    method_2_api_gateway_with_polling()
    
    # Method 3: Test API Gateway with simpler request
    method_3_test_api_gateway_simple()
    
    # Method 4: Show curl examples
    create_curl_examples()
    
    print("\n🎉 Summary:")
    print("✅ Method 1 (Direct Lambda): Best for full JSON output")
    print("⏰ Method 2-3 (API Gateway): Will timeout but Lambda completes")
    print("💡 Recommendation: Use Method 1 for reliable full JSON results")

if __name__ == "__main__":
    main()

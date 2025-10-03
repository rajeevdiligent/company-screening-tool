#!/usr/bin/env python3
"""
Practical methods to get full JSON data from API Gateway calls
"""

import json
import requests
import time
import boto3
import asyncio
from datetime import datetime

API_ENDPOINT = "https://6kwwwts1z6.execute-api.us-east-1.amazonaws.com/prod/search"

class APIGatewayDataRetriever:
    """Handle different methods to get data from API Gateway"""
    
    def __init__(self):
        self.api_endpoint = API_ENDPOINT
        self.session = boto3.Session(profile_name='diligent')
        self.lambda_client = self.session.client('lambda', region_name='us-east-1')
        self.logs_client = self.session.client('logs', region_name='us-east-1')
    
    def method_1_async_with_polling(self, company_name):
        """
        Method 1: Start API Gateway call, then poll CloudWatch logs for results
        """
        print(f"🚀 Method 1: Async API Gateway + Log Polling for {company_name}")
        print("=" * 60)
        
        # Step 1: Start the API Gateway request (will timeout)
        print("📤 Starting API Gateway request...")
        start_time = time.time()
        
        try:
            response = requests.post(
                self.api_endpoint,
                json={"company_name": company_name},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            print(f"📊 API Gateway Status: {response.status_code}")
        except requests.exceptions.Timeout:
            print("⏰ API Gateway timed out (expected)")
        
        print("🔍 Lambda function is now running in background...")
        print("📋 Polling CloudWatch logs for completion...")
        
        # Step 2: Poll logs for completion (simplified approach)
        print("💡 For now, use direct Lambda invocation for immediate results")
        print("🔧 Future enhancement: Implement log polling or use SQS/SNS")
        
        return None
    
    def method_2_direct_lambda_fallback(self, company_name):
        """
        Method 2: Try API Gateway, fallback to direct Lambda
        """
        print(f"🚀 Method 2: API Gateway with Direct Lambda Fallback for {company_name}")
        print("=" * 60)
        
        # Try API Gateway first
        print("📤 Attempting API Gateway...")
        try:
            response = requests.post(
                self.api_endpoint,
                json={"company_name": company_name},
                headers={"Content-Type": "application/json"},
                timeout=35  # Slightly longer timeout
            )
            
            if response.status_code == 200:
                print("✅ API Gateway succeeded!")
                return response.json()
            else:
                print(f"⏰ API Gateway returned {response.status_code}")
        except requests.exceptions.Timeout:
            print("⏰ API Gateway timed out")
        
        # Fallback to direct Lambda
        print("🔄 Falling back to direct Lambda invocation...")
        return self.direct_lambda_invoke(company_name)
    
    def method_3_direct_lambda_invoke(self, company_name):
        """
        Method 3: Direct Lambda invocation (most reliable)
        """
        print(f"🚀 Method 3: Direct Lambda Invocation for {company_name}")
        print("=" * 60)
        
        return self.direct_lambda_invoke(company_name)
    
    def method_4_webhook_simulation(self, company_name):
        """
        Method 4: Simulate webhook pattern for web applications
        """
        print(f"🚀 Method 4: Webhook Pattern Simulation for {company_name}")
        print("=" * 60)
        
        # In a real implementation, you would:
        # 1. Start API Gateway request with a callback URL
        # 2. Lambda would POST results to your webhook when complete
        # 3. Your app would receive the full JSON via webhook
        
        print("📋 Webhook Pattern Steps:")
        print("1. 📤 POST to API Gateway with callback_url")
        print("2. ⏰ API Gateway times out (expected)")
        print("3. 🔄 Lambda continues processing")
        print("4. 📨 Lambda POSTs results to your webhook_url")
        print("5. ✅ Your app receives full JSON data")
        
        print("\n💡 For now, using direct Lambda as webhook simulation:")
        return self.direct_lambda_invoke(company_name)
    
    def direct_lambda_invoke(self, company_name):
        """Helper method for direct Lambda invocation"""
        payload = {"company_name": company_name}
        
        print(f"📤 Invoking Lambda directly...")
        start_time = time.time()
        
        try:
            response = self.lambda_client.invoke(
                FunctionName='company-screening-tool',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            end_time = time.time()
            print(f"⏱️ Execution time: {end_time - start_time:.2f} seconds")
            
            if response['StatusCode'] == 200:
                result = json.loads(response['Payload'].read())
                
                # Handle both direct and API Gateway response formats
                if isinstance(result.get('body'), str):
                    company_data = json.loads(result['body'])
                else:
                    company_data = result
                
                print("✅ Success! Full JSON received")
                print(f"  Company: {company_data.get('company_name')}")
                print(f"  Legal Name: {company_data.get('legal_name')}")
                print(f"  Executives: {len(company_data.get('key_executives', []))} found")
                
                # Save to file
                output_file = f"api_retrieved_{company_name.replace(' ', '_')}.json"
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

def create_web_app_example():
    """
    Example for web applications using API Gateway
    """
    print("\n🌐 Web Application Example")
    print("=" * 60)
    
    html_example = '''
<!-- HTML Frontend Example -->
<!DOCTYPE html>
<html>
<head>
    <title>Company Screening</title>
</head>
<body>
    <h1>Company Screening Tool</h1>
    <input type="text" id="companyName" placeholder="Enter company name">
    <button onclick="searchCompany()">Search</button>
    <div id="results"></div>
    
    <script>
    async function searchCompany() {
        const companyName = document.getElementById('companyName').value;
        const resultsDiv = document.getElementById('results');
        
        resultsDiv.innerHTML = 'Searching...';
        
        try {
            const response = await fetch('https://6kwwwts1z6.execute-api.us-east-1.amazonaws.com/prod/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company_name: companyName })
            });
            
            if (response.status === 504) {
                // Expected timeout - show processing message
                resultsDiv.innerHTML = `
                    <p>🔄 Processing ${companyName}...</p>
                    <p>⏰ This may take 1-2 minutes due to comprehensive data gathering</p>
                    <p>💡 For immediate results, use the direct Lambda method</p>
                `;
                
                // In a real app, you would:
                // 1. Poll a status endpoint
                // 2. Use WebSockets for real-time updates
                // 3. Implement a job queue system
                
            } else if (response.ok) {
                const data = await response.json();
                displayResults(data);
            }
            
        } catch (error) {
            resultsDiv.innerHTML = 'Search in progress (API Gateway timeout expected)';
        }
    }
    
    function displayResults(data) {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = `
            <h2>${data.legal_name}</h2>
            <p><strong>Industry:</strong> ${data.industry}</p>
            <p><strong>Stock Symbol:</strong> ${data.stock_symbol}</p>
            <p><strong>Executives:</strong> ${data.key_executives.join(', ')}</p>
        `;
    }
    </script>
</body>
</html>
    '''
    
    print("📄 Save this as 'company_search.html' for a web interface:")
    print(html_example)

def main():
    """Demonstrate all methods"""
    print("🎯 API Gateway Data Retrieval Methods")
    print("=" * 60)
    
    retriever = APIGatewayDataRetriever()
    company_name = "Tesla"
    
    print("Available methods to get full JSON data from API Gateway calls:\n")
    
    # Method 1: Async with polling (conceptual)
    retriever.method_1_async_with_polling(company_name)
    print()
    
    # Method 2: API Gateway with fallback (practical)
    print("🔧 Running Method 2 (API Gateway + Fallback)...")
    result = retriever.method_2_direct_lambda_fallback(company_name)
    if result:
        print(f"✅ Retrieved data for {result.get('legal_name', company_name)}")
    print()
    
    # Method 3: Direct Lambda (most reliable)
    # Commented out to avoid duplicate calls
    # retriever.method_3_direct_lambda_invoke(company_name)
    
    # Method 4: Webhook pattern (conceptual)
    retriever.method_4_webhook_simulation(company_name)
    
    # Web app example
    create_web_app_example()
    
    print("\n🎉 Summary:")
    print("✅ Method 2 (API Gateway + Fallback): Best for applications")
    print("✅ Method 3 (Direct Lambda): Most reliable for scripts")
    print("🔮 Method 1 & 4: Future enhancements for production web apps")

if __name__ == "__main__":
    main()

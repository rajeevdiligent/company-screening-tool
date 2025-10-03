#!/usr/bin/env python3
"""
Simple API client that handles the timeout gracefully
"""

import requests
import json
import subprocess
import time
from pathlib import Path

class CompanyScreeningClient:
    """Simple client for getting company data"""
    
    def __init__(self):
        self.api_url = "https://6kwwwts1z6.execute-api.us-east-1.amazonaws.com/prod/search"
        self.output_dir = Path("outputjson")
    
    def search_company(self, company_name, method="hybrid"):
        """
        Search for company data using different methods
        
        Args:
            company_name: Name of the company to search
            method: "api", "lambda", or "hybrid" (default)
        """
        
        if method == "api":
            return self._api_gateway_only(company_name)
        elif method == "lambda":
            return self._direct_lambda(company_name)
        else:  # hybrid
            return self._hybrid_approach(company_name)
    
    def _api_gateway_only(self, company_name):
        """Try API Gateway only (will likely timeout)"""
        print(f"🚀 API Gateway search for: {company_name}")
        
        try:
            response = requests.post(
                self.api_url,
                json={"company_name": company_name},
                headers={"Content-Type": "application/json"},
                timeout=35
            )
            
            if response.status_code == 200:
                print("✅ API Gateway succeeded!")
                return response.json()
            else:
                print(f"❌ API Gateway failed: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("⏰ API Gateway timed out (expected for comprehensive searches)")
            return None
        except Exception as e:
            print(f"💥 Error: {e}")
            return None
    
    def _direct_lambda(self, company_name):
        """Use direct Lambda invocation via test script"""
        print(f"🚀 Direct Lambda search for: {company_name}")
        
        try:
            # Use your existing test script
            result = subprocess.run(
                ['./test_lambda.sh', company_name],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            if result.returncode == 0:
                # Read the generated JSON file
                output_file = self.output_dir / f"lambda_search_{company_name}.json"
                if output_file.exists():
                    with open(output_file, 'r') as f:
                        data = json.load(f)
                    print("✅ Direct Lambda succeeded!")
                    return data
                else:
                    print("❌ Output file not found")
                    return None
            else:
                print(f"❌ Lambda invocation failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"💥 Error: {e}")
            return None
    
    def _hybrid_approach(self, company_name):
        """Try API Gateway first, fallback to direct Lambda"""
        print(f"🚀 Hybrid search for: {company_name}")
        
        # Try API Gateway first (quick attempt)
        print("📤 Trying API Gateway...")
        api_result = self._api_gateway_only(company_name)
        
        if api_result:
            return api_result
        
        # Fallback to direct Lambda
        print("🔄 Falling back to direct Lambda...")
        return self._direct_lambda(company_name)
    
    def display_summary(self, data):
        """Display a summary of the company data"""
        if not data:
            print("❌ No data available")
            return
        
        print("\n" + "="*50)
        print(f"📊 Company: {data.get('company_name', 'N/A')}")
        print(f"🏢 Legal Name: {data.get('legal_name', 'N/A')}")
        print(f"🌐 Website: {data.get('website', 'N/A')}")
        print(f"📈 Stock Symbol: {data.get('stock_symbol', 'N/A')}")
        print(f"🏭 Industry: {data.get('industry', 'N/A')}")
        
        executives = data.get('key_executives', [])
        if executives:
            print(f"👥 Key Executives ({len(executives)}):")
            for exec in executives[:5]:  # Show first 5
                print(f"   • {exec}")
        
        filings = data.get('regulatory_filings', [])
        if filings:
            print(f"📋 SEC Filings: {len(filings)} found")
        
        print(f"🔍 Confidence: {data.get('confidence_level', 'N/A')}")
        print("="*50)

def main():
    """Demo the client"""
    client = CompanyScreeningClient()
    
    print("🎯 Company Screening API Client")
    print("Available methods: api, lambda, hybrid")
    print()
    
    # Example searches
    companies = ["Tesla", "Netflix"]
    
    for company in companies:
        print(f"\n🔍 Searching for: {company}")
        
        # Use hybrid approach (recommended)
        data = client.search_company(company, method="hybrid")
        client.display_summary(data)
        
        if data:
            # Save to a custom file
            output_file = f"client_output_{company.lower()}.json"
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"💾 Saved to: {output_file}")

if __name__ == "__main__":
    main()

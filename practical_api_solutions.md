# How to Get Data from API Gateway Calls

## 🎯 **The Challenge**
- API Gateway times out after 29 seconds
- Lambda function takes 60-120 seconds to complete
- Lambda continues running and produces full JSON results
- **Question**: How do we get the complete data?

## 🚀 **Practical Solutions**

### **Solution 1: Hybrid Approach (Recommended for Apps)**

```python
import requests
import boto3
import json

def get_company_data_hybrid(company_name):
    """Try API Gateway, fallback to direct Lambda"""
    
    api_url = "https://6kwwwts1z6.execute-api.us-east-1.amazonaws.com/prod/search"
    
    # Step 1: Try API Gateway (quick attempt)
    try:
        print(f"🚀 Trying API Gateway for {company_name}...")
        response = requests.post(
            api_url,
            json={"company_name": company_name},
            headers={"Content-Type": "application/json"},
            timeout=35
        )
        
        if response.status_code == 200:
            print("✅ API Gateway succeeded!")
            return response.json()
            
    except requests.exceptions.Timeout:
        print("⏰ API Gateway timed out")
    
    # Step 2: Fallback to direct Lambda
    print("🔄 Using direct Lambda invocation...")
    session = boto3.Session(profile_name='diligent')
    lambda_client = session.client('lambda', region_name='us-east-1')
    
    response = lambda_client.invoke(
        FunctionName='company-screening-tool',
        InvocationType='RequestResponse',
        Payload=json.dumps({"company_name": company_name})
    )
    
    result = json.loads(response['Payload'].read())
    if isinstance(result.get('body'), str):
        return json.loads(result['body'])
    return result

# Usage
data = get_company_data_hybrid("Apple")
print(json.dumps(data, indent=2))
```

### **Solution 2: Direct Lambda (Most Reliable)**

```bash
# Command line (what you're already using successfully)
./test_lambda.sh "Apple"

# AWS CLI direct
aws lambda invoke \
  --function-name company-screening-tool \
  --payload '{"company_name": "Apple"}' \
  --profile diligent \
  apple_output.json
```

### **Solution 3: Web Application Pattern**

```javascript
// Frontend JavaScript
async function searchCompany(companyName) {
    const apiUrl = "https://6kwwwts1z6.execute-api.us-east-1.amazonaws.com/prod/search";
    
    // Show loading state
    showLoading(`Searching for ${companyName}...`);
    
    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company_name: companyName })
        });
        
        if (response.status === 504) {
            // Expected timeout - show processing message
            showProcessing(companyName);
            
            // Option A: Poll a status endpoint (you'd need to implement)
            // Option B: Use WebSockets for real-time updates
            // Option C: Redirect to results page that polls
            
            return { status: "processing" };
        }
        
        if (response.ok) {
            const data = await response.json();
            displayResults(data);
            return data;
        }
        
    } catch (error) {
        console.log("API Gateway timeout (expected)");
        showProcessing(companyName);
    }
}

function showProcessing(companyName) {
    document.getElementById('results').innerHTML = `
        <div class="processing">
            <h3>🔄 Processing ${companyName}</h3>
            <p>⏰ Comprehensive data gathering in progress...</p>
            <p>💡 This typically takes 1-2 minutes</p>
            <p>🔧 For immediate results, use the direct Lambda method</p>
        </div>
    `;
}
```

### **Solution 4: Async Job Pattern (Future Enhancement)**

```python
# Enhanced Lambda handler for async processing
def lambda_handler_async(event, context):
    """Enhanced handler with job tracking"""
    
    company_name = event.get('company_name')
    callback_url = event.get('callback_url')  # Optional webhook
    job_id = event.get('job_id', str(uuid.uuid4()))
    
    if callback_url:
        # Start processing in background
        # When complete, POST results to callback_url
        threading.Thread(
            target=process_and_callback,
            args=(company_name, callback_url, job_id)
        ).start()
        
        return {
            'statusCode': 202,  # Accepted
            'body': json.dumps({
                'job_id': job_id,
                'status': 'processing',
                'message': f'Started processing {company_name}'
            })
        }
    else:
        # Synchronous processing (current behavior)
        return process_company_sync(company_name)
```

## 📊 **Comparison of Solutions**

| Solution | Speed | Reliability | Complexity | Best For |
|----------|-------|-------------|------------|----------|
| **Hybrid Approach** | ⚡ Fast | ✅ High | 🟡 Medium | Applications |
| **Direct Lambda** | ⚡ Fast | ✅ Perfect | 🟢 Simple | Scripts/Testing |
| **Web App Pattern** | ⏰ Timeout | 🟡 Partial | 🟡 Medium | User Interfaces |
| **Async Job Pattern** | ⚡ Fast | ✅ High | 🔴 Complex | Production Apps |

## 🎯 **Immediate Solutions You Can Use Now**

### **For Scripts/Testing:**
```bash
# Your existing method (works perfectly!)
./test_lambda.sh "Apple"
```

### **For Python Applications:**
```python
import subprocess
import json

def get_company_data(company_name):
    """Use your existing test script"""
    result = subprocess.run(
        ['./test_lambda.sh', company_name],
        capture_output=True,
        text=True
    )
    
    # Read the generated JSON file
    with open(f'outputjson/lambda_search_{company_name}.json', 'r') as f:
        return json.load(f)

# Usage
apple_data = get_company_data("Apple")
print(f"Company: {apple_data['legal_name']}")
```

### **For Web Applications:**
```bash
# Create a simple API endpoint that calls your Lambda
# and returns the results when ready
curl -X POST "your-backend/api/company-search" \
  -d '{"company_name": "Apple"}' \
  -H "Content-Type: application/json"
```

## ✅ **Bottom Line**

**Your API Gateway is working perfectly!** The timeout is just an AWS limitation. Here are your options:

1. **🚀 Keep using `./test_lambda.sh`** - It works great!
2. **🔄 Use the hybrid approach** - Try API Gateway, fallback to direct Lambda
3. **🌐 For web apps** - Implement async processing with status updates
4. **⚡ For immediate results** - Always use direct Lambda invocation

**The comprehensive JSON data you want is being generated successfully** - it's just a matter of choosing the right retrieval method for your use case!

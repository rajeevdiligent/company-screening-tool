#!/bin/bash

# Test Lambda Function and Extract JSON Content
# Usage: ./test_lambda.sh "Company Name"

if [ $# -eq 0 ]; then
    echo "Usage: $0 \"Company Name\""
    echo "Example: $0 \"Apple Inc\""
    exit 1
fi

COMPANY_NAME="$1"
SAFE_NAME=$(echo "$COMPANY_NAME" | sed 's/[^a-zA-Z0-9]/_/g')
TEMP_RESPONSE="temp_response_${SAFE_NAME}.json"
OUTPUT_FILE="outputjson/lambda_search_${SAFE_NAME}.json"

echo "🔍 Testing Lambda function with: $COMPANY_NAME"
echo "📄 Output will be saved to: $OUTPUT_FILE"

# Invoke Lambda function
aws lambda invoke \
    --function-name company-screening-tool \
    --payload "{\"company_name\": \"$COMPANY_NAME\"}" \
    --profile diligent \
    --cli-read-timeout 0 \
    --cli-connect-timeout 60 \
    "$TEMP_RESPONSE"

# Check if the invocation was successful
if [ $? -eq 0 ]; then
    echo "✅ Lambda invocation successful"
    
    # Extract and format the JSON content
    python3 -c "
import json
import sys

try:
    with open('$TEMP_RESPONSE', 'r') as f:
        response = json.load(f)
    
    if 'body' in response:
        # Extract the body content and parse it
        body_content = json.loads(response['body'])
        
        # Save the formatted company data
        with open('$OUTPUT_FILE', 'w') as f:
            json.dump(body_content, f, indent=2)
        
        print('✅ Company data saved to $OUTPUT_FILE')
        
        # Display summary
        print(f'📊 Company: {body_content.get(\"company_name\", \"N/A\")}')
        print(f'🏢 Legal Name: {body_content.get(\"legal_name\", \"N/A\")}')
        print(f'🌐 Website: {body_content.get(\"website\", \"N/A\")}')
        print(f'📈 Stock Symbol: {body_content.get(\"stock_symbol\", \"N/A\")}')
        
        # Show key executives
        executives = body_content.get('key_executives', [])
        if executives:
            print('👥 Key Executives:')
            for exec in executives[:3]:  # Show first 3
                print(f'   • {exec}')
    else:
        print('❌ Error: No body content in response')
        print(json.dumps(response, indent=2))
        
except Exception as e:
    print(f'❌ Error processing response: {e}')
    sys.exit(1)
"
    
    # Clean up temp file
    rm "$TEMP_RESPONSE"
    
else
    echo "❌ Lambda invocation failed"
    exit 1
fi

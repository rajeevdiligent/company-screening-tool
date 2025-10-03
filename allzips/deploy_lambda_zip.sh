#!/bin/bash

# Lambda Deployment Script
# Creates and deploys a Lambda function package

set -e

echo "🚀 Lambda Deployment Script"
echo "=========================="

# Configuration
FUNCTION_NAME="company-screening-tool"
REGION="us-east-1"
PROFILE="diligent"

# Create the deployment package
echo "📦 Creating Lambda deployment package..."
python create_lambda_zip.py

# Find the most recent zip file
ZIP_FILE=$(ls -t company-screening-lambda-*.zip | head -n1)

if [ ! -f "$ZIP_FILE" ]; then
    echo "❌ No zip file found!"
    exit 1
fi

echo "📁 Using package: $ZIP_FILE"
echo "📊 Package size: $(du -h "$ZIP_FILE" | cut -f1)"

# Check if function exists
echo "🔍 Checking if Lambda function exists..."
if aws lambda get-function --function-name "$FUNCTION_NAME" --profile "$PROFILE" --region "$REGION" >/dev/null 2>&1; then
    echo "✅ Function exists, updating code..."
    
    # Update function code
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE" \
        --profile "$PROFILE" \
        --region "$REGION"
    
    echo "✅ Function code updated successfully!"
    
else
    echo "⚠️ Function does not exist. Please create it first using SAM deploy or AWS Console."
    echo "📋 To create the function, run:"
    echo "   sam deploy --guided"
    exit 1
fi

# Get function info
echo "📋 Function Information:"
aws lambda get-function \
    --function-name "$FUNCTION_NAME" \
    --profile "$PROFILE" \
    --region "$REGION" \
    --query 'Configuration.{FunctionName:FunctionName,Runtime:Runtime,MemorySize:MemorySize,Timeout:Timeout,LastModified:LastModified}' \
    --output table

echo ""
echo "🎉 Deployment completed successfully!"
echo "🔧 Function: $FUNCTION_NAME"
echo "📦 Package: $ZIP_FILE"
echo "🌍 Region: $REGION"

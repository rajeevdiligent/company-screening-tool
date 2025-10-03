#!/usr/bin/env python3
"""
Create a fresh Lambda deployment package specifically for API Gateway integration
"""

import os
import shutil
import zipfile
import tempfile
from pathlib import Path

def create_api_lambda_package():
    """Create a Lambda package with API Gateway support"""
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print(f"📁 Creating API Gateway Lambda package in: {temp_path}")
        
        # Create the lambda_handler.py with API Gateway support
        lambda_handler_code = '''#!/usr/bin/env python3
"""
AWS Lambda Handler for Company Screening Tool with API Gateway Support
"""

import json
import os
import asyncio
import logging
from typing import Dict, Any
from optimized_company_search import OptimizedCompanySearcher

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for company screening with API Gateway support
    """
    
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Handle both API Gateway and direct Lambda invocation
        company_name = None
        is_api_gateway = False
        
        # Check if this is an API Gateway request
        if 'httpMethod' in event and 'body' in event:
            is_api_gateway = True
            logger.info("Detected API Gateway request")
            
            try:
                if event.get('body'):
                    body = json.loads(event['body'])
                    company_name = body.get('company_name')
                    logger.info(f"Extracted company_name from API Gateway body: {company_name}")
                else:
                    logger.warning("API Gateway request has empty body")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse API Gateway body: {e}")
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                    },
                    'body': json.dumps({
                        'error': 'Invalid JSON in request body'
                    })
                }
        else:
            # Direct Lambda invocation
            logger.info("Detected direct Lambda invocation")
            company_name = event.get('company_name')
        
        if not company_name:
            error_response = {
                'error': 'Missing required parameter: company_name',
                'usage': 'Provide company_name in the request body (API Gateway) or event payload (direct invocation)'
            }
            
            if is_api_gateway:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                    },
                    'body': json.dumps(error_response)
                }
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps(error_response)
                }
        
        logger.info(f"Starting company research for: {company_name}")
        
        # Validate environment variables
        serper_key = os.environ.get('SERPER_API_KEY')
        if not serper_key:
            error_response = {
                'error': 'SERPER_API_KEY environment variable not configured'
            }
            
            if is_api_gateway:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(error_response)
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps(error_response)
                }
        
        # Initialize company searcher
        searcher = OptimizedCompanySearcher()
        
        # Run the async search function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            company_info = loop.run_until_complete(
                searcher.search_company(company_name)
            )
        finally:
            loop.close()
        
        # Convert to dictionary for JSON serialization
        if hasattr(company_info, '__dict__'):
            result = company_info.__dict__
        else:
            result = company_info
        
        # Add metadata
        result['lambda_execution'] = {
            'request_id': context.aws_request_id,
            'function_name': context.function_name,
            'function_version': context.function_version,
            'memory_limit': context.memory_limit_in_mb,
            'remaining_time': context.get_remaining_time_in_millis()
        }
        
        logger.info(f"Successfully completed research for: {company_name}")
        
        # Return response based on invocation type
        if is_api_gateway:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps(result, indent=2, default=str)
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps(result, indent=2, default=str)
            }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        
        error_response = {
            'error': 'Internal server error',
            'message': str(e),
            'request_id': getattr(context, 'aws_request_id', 'unknown')
        }
        
        if is_api_gateway:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(error_response)
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps(error_response)
            }
'''
        
        # Write the lambda handler
        with open(temp_path / 'lambda_handler.py', 'w') as f:
            f.write(lambda_handler_code)
        
        # Copy other Python files
        src_dir = Path('/Users/rchandran/Library/CloudStorage/OneDrive-DiligentCorporation/TPMAI/SCREENING/src')
        for py_file in ['optimized_company_search.py', 'sec_filing_enhancer.py', 'search_based_sec_extractor.py']:
            if (src_dir / py_file).exists():
                shutil.copy2(src_dir / py_file, temp_path / py_file)
                print(f"✅ Copied {py_file}")
        
        # Install dependencies
        print("📦 Installing dependencies...")
        os.system(f"pip install -r {src_dir}/requirements-lambda.txt -t {temp_path} --quiet")
        
        # Create zip file
        zip_name = "api-gateway-lambda-package.zip"
        zip_path = Path('/Users/rchandran/Library/CloudStorage/OneDrive-DiligentCorporation/TPMAI/SCREENING') / zip_name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(temp_path)
                    zipf.write(file_path, arcname)
        
        print(f"✅ Created: {zip_path}")
        print(f"📊 Size: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        return str(zip_path)

if __name__ == "__main__":
    create_api_lambda_package()

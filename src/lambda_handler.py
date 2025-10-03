#!/usr/bin/env python3
"""
AWS Lambda Handler for Company Screening Tool

This Lambda function provides company research capabilities with enhanced
SEC filing searches and aggressive executive data extraction.

Environment Variables Required:
- SERPER_API_KEY: API key for SERPER search service
- AWS_REGION: AWS region (default: us-east-1)

Usage:
    Event format:
    {
        "company_name": "Apple Inc",
        "output_format": "json"  # optional, defaults to json
    }
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
    AWS Lambda handler for company screening
    
    Args:
        event: Lambda event containing company_name
        context: Lambda context object
        
    Returns:
        Dict containing company information or error message
    """
    
    try:
        # Extract company name from event
        company_name = event.get('company_name')
        if not company_name:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameter: company_name',
                    'usage': 'Provide company_name in the event payload'
                })
            }
        
        logger.info(f"Starting company research for: {company_name}")
        
        # Validate environment variables
        serper_key = os.environ.get('SERPER_API_KEY')
        if not serper_key:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'SERPER_API_KEY environment variable not configured'
                })
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
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS'
            },
            'body': json.dumps(result, indent=2, default=str)
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e),
                'request_id': getattr(context, 'aws_request_id', 'unknown')
            })
        }

def test_handler():
    """Test function for local development"""
    
    class MockContext:
        aws_request_id = "test-request-123"
        function_name = "company-screening-test"
        function_version = "1"
        memory_limit_in_mb = 512
        
        def get_remaining_time_in_millis(self):
            return 30000
    
    # Test event
    test_event = {
        "company_name": "Apple Inc"
    }
    
    # Set environment variables for testing
    os.environ['SERPER_API_KEY'] = os.environ.get('SERPER_API_KEY', 'test-key')
    os.environ['AWS_REGION'] = 'us-east-1'
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_handler()

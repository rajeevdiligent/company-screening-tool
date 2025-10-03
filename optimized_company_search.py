#!/usr/bin/env python3
"""
Optimized Company Search Tool

This script incorporates all successful patterns from previous searches to ensure
maximum field completion. Based on successful extractions from Tesla, Walmart, and others.

Key Success Patterns Integrated:
- EDGAR filing targeting (Commission File Numbers)
- SEC 10-K specific searches
- Enhanced FORM 10-K searches for non-listed companies
- Enhanced FORM 20-F searches for foreign companies
- Enhanced FORM 8-K searches for current events and material changes
- Enhanced DEF 14A Proxy Statement searches for executive and governance data
- COMPANY-SPECIFIC search queries with business entity keywords
- EXCLUSION filters to eliminate people, products, and non-corporate entities
- AGGRESSIVE CRUNCHBASE searches (12 queries) for private company executives
- AGGRESSIVE PITCHBOOK searches (12 queries) for private equity management data
- AGGRESSIVE LINKEDIN searches (15 queries) for current executive profiles
- Wikipedia comprehensive coverage
- Multiple identifier extraction (LEI, DUNS, EIN, CIK)
- Enhanced executive and financial data targeting for private companies

Usage:
    python optimized_company_search.py --company "Company Name"
"""

import os
import json
import asyncio
import argparse
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

import requests
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimized_company_search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CompanyInfo:
    """Optimized data structure for complete company information"""
    company_name: str
    legal_name: str = ""
    official_name: str = ""
    registration_number: str = ""
    incorporation_date: str = ""
    incorporation_country: str = ""
    jurisdiction: str = ""
    business_type: str = ""
    industry: str = ""
    headquarters: str = ""
    address: str = ""
    website: str = ""
    description: str = ""
    products_services: str = ""
    alternate_names: List[str] = None
    identifiers: Dict[str, str] = None
    key_executives: List[str] = None
    subsidiaries: List[str] = None
    parent_company: str = ""
    stock_symbol: str = ""
    market_cap: str = ""
    revenue: str = ""
    annual_revenue: str = ""
    employees: str = ""
    founded_year: str = ""
    regulatory_filings: List[str] = None
    sources: List[str] = None
    confidence_level: str = ""
    last_updated: str = ""
    
    def __post_init__(self):
        if self.key_executives is None:
            self.key_executives = []
        if self.subsidiaries is None:
            self.subsidiaries = []
        if self.regulatory_filings is None:
            self.regulatory_filings = []
        if self.sources is None:
            self.sources = []
        if self.alternate_names is None:
            self.alternate_names = []
        if self.identifiers is None:
            self.identifiers = {}
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
        
        # Sync fields for backward compatibility
        if self.legal_name and not self.official_name:
            self.official_name = self.legal_name
        elif self.official_name and not self.legal_name:
            self.legal_name = self.official_name
        
        if self.headquarters and not self.address:
            self.address = self.headquarters
        elif self.address and not self.headquarters:
            self.headquarters = self.address
            
        if self.revenue and not self.annual_revenue:
            self.annual_revenue = self.revenue
        elif self.annual_revenue and not self.revenue:
            self.revenue = self.annual_revenue

class SerperAPI:
    """Optimized SERPER API interface"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"
        self.headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
    
    def search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """Perform optimized web search"""
        try:
            payload = {
                "q": query,
                "num": num_results,
                "gl": "us",
                "hl": "en"
            }
            
            logger.info(f"Searching: {query}")
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"SERPER API error: {e}")
            return {"organic": [], "error": str(e)}

class AWSNovaLLM:
    """Optimized AWS Nova Pro LLM interface"""
    
    def __init__(self, profile_name: str = "diligent", region: str = "us-east-1"):
        self.profile_name = profile_name
        self.region = region
        self.session = None
        self.bedrock_client = None
        self._initialize_aws_session()
    
    def _initialize_aws_session(self):
        """Initialize AWS session"""
        try:
            self.session = boto3.Session(profile_name=self.profile_name)
            self.bedrock_client = self.session.client(
                'bedrock-runtime',
                region_name=self.region
            )
            logger.info(f"AWS session initialized with profile: {self.profile_name}")
            
        except NoCredentialsError:
            logger.error(f"AWS credentials not found for profile: {self.profile_name}")
            raise
        except Exception as e:
            logger.error(f"AWS initialization error: {e}")
            raise
    
    def analyze_company_data(self, search_results: List[Dict], company_name: str) -> Dict[str, Any]:
        """Analyze search results with optimized prompt"""
        try:
            prompt = self._create_optimized_prompt(search_results, company_name)
            
            response = self.bedrock_client.invoke_model(
                modelId="amazon.nova-pro-v1:0",
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    "inferenceConfig": {
                        "max_new_tokens": 4000,
                        "temperature": 0.1
                    }
                }),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            output = response_body.get('output', {})
            message = output.get('message', {})
            content = message.get('content', [])
            analysis = content[0].get('text', '') if content else ''
            
            return self._parse_llm_response(analysis)
            
        except ClientError as e:
            logger.error(f"AWS Bedrock error: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            return {"error": str(e)}
    
    def _create_optimized_prompt(self, search_results: List[Dict], company_name: str) -> str:
        """Create optimized prompt based on successful patterns"""
        
        formatted_results = []
        for i, result in enumerate(search_results[:15], 1):  # More results for analysis
            title = result.get('title', 'No title')
            snippet = result.get('snippet', 'No snippet')
            link = result.get('link', 'No link')
            formatted_results.append(f"{i}. Title: {title}\n   Snippet: {snippet}\n   Source: {link}\n")
        
        search_data = "\n".join(formatted_results)
        
        prompt = f"""
You are an expert business researcher. Extract COMPLETE information about {company_name} AS A COMPANY/CORPORATION from the search results.

CRITICAL: Focus ONLY on {company_name} as a BUSINESS ENTITY. Ignore any results about:
- People with the same name (individuals, celebrities, athletes, politicians)
- Products or services with the same name
- Places or locations with the same name
- Other non-corporate entities

SEARCH RESULTS:
{search_data}

CRITICAL SUCCESS PATTERNS (from Tesla: 001-34756, Walmart: 001-06991):
1. REGISTRATION NUMBERS are found in SEC filings as "Commission File Number: 001-XXXXX"
2. INCORPORATION DATES are in SEC 10-K filings and Wikipedia infoboxes
3. ALL IDENTIFIERS (LEI, DUNS, EIN, CIK) are extractable from comprehensive searches
4. EXECUTIVE NAMES come from recent SEC filings and corporate websites
5. FINANCIAL DATA is in annual reports and financial news sources
6. NON-LISTED COMPANIES may still file FORM 10-K with SEC - check these thoroughly
7. FORM 10-K filings contain incorporation details even for private companies
8. FOREIGN COMPANIES file FORM 20-F with SEC - critical for international companies
9. FORM 20-F contains jurisdiction, incorporation country, and registration details
10. FORM 8-K filings contain current events, executive changes, and material information
11. DEF 14A Proxy Statements contain detailed executive information and governance data
12. CRUNCHBASE profiles contain comprehensive executive data for private companies
13. PITCHBOOK provides detailed management information for private equity-backed companies
14. LINKEDIN profiles show current executive positions and recent leadership changes
15. For PRIVATE/ACQUIRED companies, prioritize Crunchbase, PitchBook, and LinkedIn over SEC filings

MANDATORY FIELD COMPLETION:
- legal_name: Extract from SEC filing headers or Wikipedia infobox
- registration_number: Look for "001-XXXXX" or "File No. XXXXXXX" patterns
- incorporation_date: Find in SEC filings or Wikipedia (format: YYYY-MM-DD)
- incorporation_country: Usually "United States" for US companies
- jurisdiction: Look for "Delaware" or other state incorporation
- business_type: "Corporation", "LLC", "Partnership"
- industry: Primary business sector
- headquarters: Complete address from corporate websites
- website: Official corporate website URL
- description: Business description from official sources
- products_services: Main offerings from business descriptions
- alternate_names: Former names, abbreviations, trade names
- identifiers: Extract LEI, DUNS, EIN, CIK when mentioned
- key_executives: CEO, CFO, CTO, COO from Crunchbase/PitchBook/LinkedIn (prioritize current data)
- subsidiaries: Major subsidiary companies
- stock_symbol: NYSE/NASDAQ ticker
- market_cap: Current market capitalization
- annual_revenue: Latest annual revenue with year
- employees: Current employee count
- founded_year: Year company was founded
- regulatory_filings: SEC filing URLs when found

PROVEN SUCCESSFUL SOURCES (PRIORITIZED FOR EXECUTIVE DATA):
- SEC EDGAR filings (highest priority for registration numbers)
- SEC FORM 10-K filings (critical for non-listed companies)
- SEC FORM 20-F filings (essential for foreign companies on US exchanges)
- SEC FORM 8-K filings (current events, executive changes, material information)
- SEC DEF 14A Proxy Statements (executive compensation, governance, board details)
- CRUNCHBASE (CRITICAL for private company executives, CEO/CFO data, management teams)
- PITCHBOOK (ESSENTIAL for private equity companies, executive profiles, board members)
- LINKEDIN (VITAL for current executive information, C-suite profiles, leadership teams)
- Wikipedia company pages (comprehensive overview data)
- Corporate websites (official information)
- Financial databases (Bloomberg, Reuters, Yahoo Finance)
- Business directories (OpenCorporates)

EXTRACTION REQUIREMENTS:
1. Fill EVERY field - no empty fields allowed if data exists
2. Use "Not available" only if truly not found after thorough search
3. Cross-reference multiple sources for accuracy
4. Prioritize official sources (SEC, corporate websites)
5. Include confidence level: High (official sources), Medium (reliable sources), Low (limited sources)

Respond with ONLY a JSON object containing all fields:
{{
    "legal_name": "Official legal company name",
    "registration_number": "Commission File Number or incorporation number",
    "incorporation_date": "YYYY-MM-DD format",
    "incorporation_country": "Country of incorporation",
    "jurisdiction": "State/province and country",
    "business_type": "Corporation/LLC/Partnership",
    "industry": "Primary industry sector",
    "headquarters": "Complete headquarters address",
    "website": "Official website URL",
    "description": "Business description",
    "products_services": "Main products and services",
    "alternate_names": ["Alternative names", "Former names"],
    "identifiers": {{
        "LEI": "Legal Entity Identifier",
        "DUNS": "DUNS number",
        "EIN": "Employer ID Number",
        "CIK": "SEC Central Index Key"
    }},
    "key_executives": ["Name - Title", "Name - Title"],
    "subsidiaries": ["Subsidiary 1", "Subsidiary 2"],
    "parent_company": "Parent company if applicable",
    "stock_symbol": "Stock ticker",
    "market_cap": "Market capitalization with currency",
    "annual_revenue": "Revenue with year and currency",
    "employees": "Employee count with year",
    "founded_year": "Year founded",
    "regulatory_filings": ["SEC filing URLs"],
    "sources": ["Source URLs"],
    "confidence_level": "High/Medium/Low"
}}
"""
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response and extract structured data"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                logger.warning("No JSON found in LLM response")
                return {"error": "Invalid response format", "raw_response": response_text}
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {"error": "JSON parsing failed", "raw_response": response_text}

class OptimizedCompanySearcher:
    """Optimized company research orchestration"""
    
    def __init__(self):
        self.serper_api = None
        self.nova_llm = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all services"""
        serper_key = os.getenv('SERPER_API_KEY')
        if not serper_key:
            raise ValueError("SERPER_API_KEY not found in environment variables")
        
        self.serper_api = SerperAPI(serper_key)
        
        aws_profile = os.getenv('AWS_PROFILE', 'diligent')
        aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        self.nova_llm = AWSNovaLLM(aws_profile, aws_region)
        
        logger.info("All services initialized successfully")
    
    def generate_optimized_queries(self, company_name: str) -> List[str]:
        """Generate optimized search queries based on successful patterns"""
        
        # COMPANY-SPECIFIC core queries (exclude people, products, other entities)
        core_queries = [
            f'"{company_name}" company corporation Wikipedia',
            f'site:wikipedia.org "{company_name}" company corporation',
            f'"{company_name}" company SEC 10-K Edgar',
            f'site:sec.gov "{company_name}" corporation 10-K',
            f'"{company_name}" business entity company profile',
            f'"{company_name}" corporation headquarters address'
        ]
        
        # COMPANY-SPECIFIC registration queries (Tesla: 001-34756, Walmart: 001-06991)
        registration_queries = [
            f'"{company_name}" corporation "Commission File Number" SEC',
            f'"{company_name}" company SEC filing "001-" registration',
            f'site:sec.gov "{company_name}" corporation "Commission File Number"',
            f'"{company_name}" company EDGAR "File Number" incorporation',
            f'site:edgar.sec.gov "{company_name}" corporation incorporation',
            f'"{company_name}" company SEC 10-K "state of incorporation"',
            f'"{company_name}" corporation annual report incorporation details',
            f'"{company_name}" company proxy statement incorporation'
        ]
        
        # COMPANY-SPECIFIC SEC FORM 10-K searches for non-listed companies
        form_10k_queries = [
            f'site:sec.gov "{company_name}" corporation "FORM 10-K"',
            f'"{company_name}" company "FORM 10-K" SEC filing',
            f'site:edgar.sec.gov "{company_name}" corporation "FORM 10-K"',
            f'"{company_name}" company "FORM 10-K" incorporation details',
            f'"{company_name}" corporation "FORM 10-K" registration number',
            f'site:sec.gov "{company_name}" corporation "FORM 10-K" Delaware',
            f'"{company_name}" company "FORM 10-K" "state of incorporation"',
            f'"{company_name}" corporation "FORM 10-K" "Commission File Number"'
        ]
        
        # Enhanced SEC FORM 20-F searches for foreign companies
        form_20f_queries = [
            f'site:sec.gov "{company_name}" "FORM 20-F"',
            f'"{company_name}" "FORM 20-F" SEC filing',
            f'site:edgar.sec.gov "{company_name}" "FORM 20-F"',
            f'"{company_name}" "FORM 20-F" annual report',
            f'"{company_name}" "FORM 20-F" foreign company',
            f'site:sec.gov "{company_name}" "FORM 20-F" incorporation',
            f'"{company_name}" "FORM 20-F" "Commission File Number"',
            f'"{company_name}" "FORM 20-F" jurisdiction country'
        ]
        
        # Enhanced SEC FORM 8-K searches for current events and material changes
        form_8k_queries = [
            f'site:sec.gov "{company_name}" "FORM 8-K"',
            f'"{company_name}" "FORM 8-K" SEC filing',
            f'site:edgar.sec.gov "{company_name}" "FORM 8-K"',
            f'"{company_name}" "FORM 8-K" current report',
            f'"{company_name}" "FORM 8-K" executive changes',
            f'site:sec.gov "{company_name}" "FORM 8-K" material events',
            f'"{company_name}" "FORM 8-K" "Commission File Number"',
            f'"{company_name}" "FORM 8-K" corporate governance'
        ]
        
        # Enhanced SEC Proxy Statement (DEF 14A) searches for governance and executive data
        proxy_def14a_queries = [
            f'site:sec.gov "{company_name}" "DEF 14A"',
            f'"{company_name}" "DEF 14A" SEC filing',
            f'site:edgar.sec.gov "{company_name}" "DEF 14A"',
            f'"{company_name}" "Proxy Statement" SEC',
            f'"{company_name}" "DEF 14A" executive compensation',
            f'site:sec.gov "{company_name}" "Proxy Statement" executives',
            f'"{company_name}" "DEF 14A" board of directors',
            f'"{company_name}" "Proxy Statement" corporate governance'
        ]
        
        # Proven identifier extraction queries
        identifier_queries = [
            f'"{company_name}" LEI identifier',
            f'"{company_name}" DUNS number',
            f'"{company_name}" EIN tax ID',
            f'"{company_name}" CIK SEC number',
            f'"{company_name}" CUSIP identifier'
        ]
        
        # COMPANY-SPECIFIC executive and financial data queries
        corporate_queries = [
            f'"{company_name}" company CEO CFO executives 2024',
            f'site:sec.gov "{company_name}" corporation executive officers',
            f'"{company_name}" company annual revenue 2024 2023',
            f'"{company_name}" corporation market cap employees',
            f'"{company_name}" company headquarters address',
            f'"{company_name}" corporation subsidiaries companies'
        ]
        
        # AGGRESSIVE CRUNCHBASE SEARCHES - Company-specific for private company executive data
        crunchbase_queries = [
            f'site:crunchbase.com "{company_name}" company executives',
            f'site:crunchbase.com "{company_name}" corporation CEO CFO',
            f'site:crunchbase.com "{company_name}" company leadership team',
            f'site:crunchbase.com "{company_name}" company profile business',
            f'site:crunchbase.com "{company_name}" company funding investors',
            f'site:crunchbase.com "{company_name}" corporation board members',
            f'site:crunchbase.com "{company_name}" company management team',
            f'site:crunchbase.com "{company_name}" business key people',
            f'"{company_name}" company crunchbase executives leadership',
            f'"{company_name}" corporation crunchbase CEO CFO CTO',
            f'"{company_name}" business crunchbase company information',
            f'"{company_name}" company crunchbase profile management'
        ]
        
        # AGGRESSIVE PITCHBOOK SEARCHES - Company-specific for private equity and executive data
        pitchbook_queries = [
            f'site:pitchbook.com "{company_name}" company executives',
            f'site:pitchbook.com "{company_name}" corporation management team',
            f'site:pitchbook.com "{company_name}" company CEO CFO',
            f'site:pitchbook.com "{company_name}" company profile business',
            f'site:pitchbook.com "{company_name}" company leadership',
            f'site:pitchbook.com "{company_name}" corporation board directors',
            f'site:pitchbook.com "{company_name}" company private equity',
            f'site:pitchbook.com "{company_name}" business key personnel',
            f'"{company_name}" company pitchbook executives management',
            f'"{company_name}" corporation pitchbook CEO CFO leadership',
            f'"{company_name}" business pitchbook company data',
            f'"{company_name}" company pitchbook private company'
        ]
        
        # AGGRESSIVE LINKEDIN SEARCHES - Company-specific for current executive information
        linkedin_queries = [
            f'site:linkedin.com "{company_name}" company CEO',
            f'site:linkedin.com "{company_name}" corporation CFO',
            f'site:linkedin.com "{company_name}" company CTO',
            f'site:linkedin.com "{company_name}" company executives',
            f'site:linkedin.com "{company_name}" corporation leadership team',
            f'site:linkedin.com "{company_name}" company management',
            f'site:linkedin.com/company "{company_name}"',
            f'site:linkedin.com "{company_name}" corporation board members',
            f'site:linkedin.com "{company_name}" company senior management',
            f'site:linkedin.com "{company_name}" business C-suite',
            f'"{company_name}" company linkedin CEO profile',
            f'"{company_name}" corporation linkedin CFO executive',
            f'"{company_name}" business linkedin company executives',
            f'"{company_name}" company linkedin leadership team',
            f'"{company_name}" corporation linkedin management profiles'
        ]
        
        # COMPANY-SPECIFIC enhanced data source queries
        source_queries = [
            f'site:bloomberg.com "{company_name}" company profile',
            f'site:reuters.com "{company_name}" corporation company',
            f'site:yahoo.com "{company_name}" company profile',
            f'site:opencorporates.com "{company_name}" corporation'
        ]
        
        # COMPANY-SPECIFIC business information queries
        business_queries = [
            f'"{company_name}" company products services business',
            f'"{company_name}" corporation industry sector business type',
            f'"{company_name}" company corporate website official',
            f'"{company_name}" corporation founded established history'
        ]
        
        # COMPANY-SPECIFIC name variation queries with business entity suffixes
        variations = []
        if "Inc" not in company_name and "Corp" not in company_name:
            variations.extend([
                f'"{company_name} Inc" company SEC filings',
                f'"{company_name} Corporation" company Wikipedia',
                f'"{company_name} Corp" company information',
                f'"{company_name} LLC" business entity',
                f'"{company_name} Ltd" corporation company'
            ])
        
        # EXCLUSION-ENHANCED queries to filter out people, products, places
        exclusion_queries = [
            f'"{company_name}" company business -person -individual -biography',
            f'"{company_name}" corporation entity -product -service -location',
            f'"{company_name}" business headquarters -celebrity -athlete -politician',
            f'"{company_name}" company profile -personal -individual -biography'
        ]
        
        # Combine all COMPANY-SPECIFIC optimized queries with exclusions prioritized
        all_queries = (
            core_queries +
            exclusion_queries +       # HIGH PRIORITY: Filter out non-company entities
            registration_queries +
            form_10k_queries +
            form_20f_queries +
            form_8k_queries +
            proxy_def14a_queries +
            crunchbase_queries +      # HIGH PRIORITY: Private company executive data
            pitchbook_queries +       # HIGH PRIORITY: Private equity and management data  
            linkedin_queries +        # HIGH PRIORITY: Current executive profiles
            identifier_queries +
            corporate_queries +
            source_queries +
            business_queries +
            variations
        )
        
        return all_queries
    
    async def search_company(self, company_name: str) -> CompanyInfo:
        """Perform optimized company search"""
        logger.info(f"Starting optimized search for: {company_name}")
        
        company_info = CompanyInfo(company_name=company_name)
        
        try:
            search_queries = self.generate_optimized_queries(company_name)
            
            # Perform searches with optimized result counts
            all_search_results = []
            for i, query in enumerate(search_queries):
                # Higher result counts for proven successful query types
                if i < 6:  # Core queries (increased from 4 to 6)
                    num_results = 12
                elif i < 10:  # Exclusion queries (NEW - filter non-company entities)
                    num_results = 15
                elif i < 18:  # Registration queries (highest priority)
                    num_results = 15
                elif i < 26:  # FORM 10-K queries (high priority for non-listed companies)
                    num_results = 15
                elif i < 34:  # FORM 20-F queries (high priority for foreign companies)
                    num_results = 15
                elif i < 42:  # FORM 8-K queries (high priority for current events)
                    num_results = 12
                elif i < 50:  # DEF 14A Proxy queries (high priority for executive data)
                    num_results = 12
                elif i < 62:  # CRUNCHBASE queries (CRITICAL for private company executives)
                    num_results = 15
                elif i < 74:  # PITCHBOOK queries (CRITICAL for private equity data)
                    num_results = 15
                elif i < 89:  # LINKEDIN queries (CRITICAL for current executive profiles)
                    num_results = 15
                elif i < 94:  # Identifier queries
                    num_results = 10
                else:  # Other queries
                    num_results = 8
                
                results = self.serper_api.search(query, num_results=num_results)
                if 'organic' in results:
                    all_search_results.extend(results['organic'])
                
                await asyncio.sleep(0.3)
            
            # Remove duplicates
            unique_results = []
            seen_urls = set()
            for result in all_search_results:
                url = result.get('link', '')
                if url and url not in seen_urls:
                    unique_results.append(result)
                    seen_urls.add(url)
            
            logger.info(f"Found {len(unique_results)} unique search results")
            
            # Analyze with Nova LLM
            if unique_results:
                analysis = self.nova_llm.analyze_company_data(unique_results, company_name)
                
                if 'error' not in analysis:
                    self._update_company_info(company_info, analysis, unique_results)
                else:
                    logger.error(f"LLM analysis failed: {analysis['error']}")
            
            return company_info
            
        except Exception as e:
            logger.error(f"Search failed for {company_name}: {e}")
            company_info.sources = [f"Error: {str(e)}"]
            return company_info
    
    def _update_company_info(self, company_info: CompanyInfo, analysis: Dict, search_results: List[Dict]):
        """Update company info with analysis results"""
        
        # Map all fields from analysis
        field_mapping = {
            'legal_name': 'legal_name',
            'registration_number': 'registration_number',
            'incorporation_date': 'incorporation_date',
            'incorporation_country': 'incorporation_country',
            'jurisdiction': 'jurisdiction',
            'business_type': 'business_type',
            'industry': 'industry',
            'headquarters': 'headquarters',
            'website': 'website',
            'description': 'description',
            'products_services': 'products_services',
            'parent_company': 'parent_company',
            'stock_symbol': 'stock_symbol',
            'market_cap': 'market_cap',
            'annual_revenue': 'annual_revenue',
            'employees': 'employees',
            'founded_year': 'founded_year',
            'confidence_level': 'confidence_level'
        }
        
        for analysis_key, info_key in field_mapping.items():
            if analysis_key in analysis and analysis[analysis_key]:
                setattr(company_info, info_key, analysis[analysis_key])
        
        # Handle list and dict fields
        if 'key_executives' in analysis and analysis['key_executives']:
            company_info.key_executives = analysis['key_executives']
        
        if 'subsidiaries' in analysis and analysis['subsidiaries']:
            company_info.subsidiaries = analysis['subsidiaries']
            
        if 'alternate_names' in analysis and analysis['alternate_names']:
            company_info.alternate_names = analysis['alternate_names']
            
        if 'identifiers' in analysis and analysis['identifiers']:
            company_info.identifiers = analysis['identifiers']
            
        if 'regulatory_filings' in analysis and analysis['regulatory_filings']:
            company_info.regulatory_filings = analysis['regulatory_filings']
        
        # Add sources from search results and analysis
        sources = []
        if 'sources' in analysis and analysis['sources']:
            sources.extend(analysis['sources'])
        
        # Add high-quality sources from search results
        for result in search_results[:10]:
            if result.get('link'):
                sources.append(result['link'])
        
        company_info.sources = list(set(sources))  # Remove duplicates
    
    def save_results(self, company_info: CompanyInfo, output_file: str = None):
        """Save optimized search results"""
        if not output_file:
            safe_name = "".join(c for c in company_info.company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            output_file = f"optimized_search_{safe_name.replace(' ', '_')}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(company_info), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return None

async def main():
    """Main function for optimized company search"""
    parser = argparse.ArgumentParser(description='Optimized company information extraction')
    parser.add_argument('--company', '-c', required=True, help='Company name to research')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize optimized searcher
        searcher = OptimizedCompanySearcher()
        
        # Perform optimized search
        print(f"🔍 Performing optimized search for: {args.company}")
        print("📊 Using proven successful patterns from Tesla and Walmart extractions...")
        
        company_info = await searcher.search_company(args.company)
        
        # Save results
        output_file = searcher.save_results(company_info, args.output)
        
        # Display comprehensive summary
        print(f"\n{'='*80}")
        print(f"🎯 OPTIMIZED COMPANY SEARCH RESULTS")
        print(f"{'='*80}")
        print(f"Company: {company_info.company_name}")
        print(f"Legal Name: {company_info.legal_name or 'Not found'}")
        print(f"Registration Number: {company_info.registration_number or 'Not found'}")
        print(f"Incorporation Date: {company_info.incorporation_date or 'Not found'}")
        print(f"Jurisdiction: {company_info.jurisdiction or 'Not found'}")
        print(f"Industry: {company_info.industry or 'Not found'}")
        print(f"Headquarters: {company_info.headquarters or 'Not found'}")
        print(f"Website: {company_info.website or 'Not found'}")
        print(f"Stock Symbol: {company_info.stock_symbol or 'Not found'}")
        print(f"Annual Revenue: {company_info.annual_revenue or 'Not found'}")
        print(f"Employees: {company_info.employees or 'Not found'}")
        print(f"Founded: {company_info.founded_year or 'Not found'}")
        
        if company_info.identifiers:
            print(f"\n📋 Identifiers:")
            for key, value in company_info.identifiers.items():
                if value and value != "Not available":
                    print(f"  {key}: {value}")
        
        if company_info.key_executives:
            print(f"\n👥 Key Executives:")
            for exec in company_info.key_executives[:3]:  # Top 3
                print(f"  • {exec}")
        
        if company_info.subsidiaries:
            print(f"\n🏢 Major Subsidiaries:")
            for sub in company_info.subsidiaries[:3]:  # Top 3
                print(f"  • {sub}")
        
        print(f"\n📊 Data Quality:")
        print(f"  Sources Found: {len(company_info.sources)}")
        print(f"  Confidence Level: {company_info.confidence_level or 'Not assessed'}")
        
        if output_file:
            print(f"\n💾 Complete results saved to: {output_file}")
        
        print(f"⏰ Search completed at: {company_info.last_updated}")
        
    except KeyboardInterrupt:
        print("\n❌ Search interrupted by user")
    except Exception as e:
        logger.error(f"Search failed: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

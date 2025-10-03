#!/usr/bin/env python3
"""
SEC Filing Enhancer

This module provides deterministic SEC filing lookup to ensure consistent
results when searching for company regulatory filings.

It acts as a fallback when the main search doesn't find SEC data consistently.
"""

import re
import requests
import json
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SECFilingEnhancer:
    """Deterministic SEC filing lookup for consistent results"""
    
    def __init__(self):
        self.sec_base_url = "https://www.sec.gov"
        self.edgar_search_url = "https://www.sec.gov/cgi-bin/browse-edgar"
        self.headers = {
            'User-Agent': 'Company Research Tool (compliance@example.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def search_company_cik(self, company_name: str) -> Optional[str]:
        """
        Search for company CIK using SEC's company search
        Returns CIK if found, None otherwise
        """
        try:
            # Clean company name for search
            clean_name = self._clean_company_name(company_name)
            
            # Try multiple search variations
            search_variations = [
                company_name,
                clean_name,
                f"{clean_name} Corporation",
                f"{clean_name} Corp",
                f"{clean_name} Inc",
            ]
            
            for search_term in search_variations:
                cik = self._search_sec_company_database(search_term)
                if cik:
                    logger.info(f"Found CIK {cik} for {company_name} using search term: {search_term}")
                    return cik
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for CIK: {e}")
            return None
    
    def _clean_company_name(self, company_name: str) -> str:
        """Clean company name for SEC search"""
        # Remove common suffixes and clean
        clean = company_name.strip()
        clean = re.sub(r'\b(Corporation|Corp|Inc|LLC|Ltd|Co)\b\.?', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
    
    def _search_sec_company_database(self, search_term: str) -> Optional[str]:
        """
        Search SEC company database for CIK
        Uses the SEC's company search endpoint
        """
        try:
            # SEC company search URL
            search_url = "https://www.sec.gov/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'company': search_term,
                'output': 'xml',
                'count': '10'
            }
            
            response = requests.get(search_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse XML response to find CIK
            content = response.text
            
            # Look for CIK pattern in XML
            cik_match = re.search(r'<CIK>(\d+)</CIK>', content)
            if cik_match:
                return cik_match.group(1).zfill(10)  # Pad with zeros to 10 digits
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching SEC database for {search_term}: {e}")
            return None
    
    def get_company_filings(self, cik: str, filing_types: List[str] = None) -> List[Dict]:
        """
        Get recent filings for a company by CIK
        
        Args:
            cik: Company CIK (Central Index Key)
            filing_types: List of filing types to search for (default: ['10-K', '10-Q', '8-K'])
        
        Returns:
            List of filing dictionaries with URLs and metadata
        """
        if filing_types is None:
            filing_types = ['10-K', '10-Q', '8-K', 'DEF 14A']
        
        try:
            filings = []
            
            for filing_type in filing_types:
                filing_data = self._get_filings_by_type(cik, filing_type)
                filings.extend(filing_data)
            
            # Sort by date (most recent first)
            filings.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            return filings[:10]  # Return top 10 most recent
            
        except Exception as e:
            logger.error(f"Error getting filings for CIK {cik}: {e}")
            return []
    
    def _get_filings_by_type(self, cik: str, filing_type: str) -> List[Dict]:
        """Get filings of specific type for a CIK"""
        try:
            search_url = "https://www.sec.gov/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'CIK': cik,
                'type': filing_type,
                'dateb': '',
                'count': '5',
                'output': 'xml'
            }
            
            response = requests.get(search_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            content = response.text
            filings = []
            
            # Parse filing entries from XML
            filing_pattern = r'<filing>.*?<type>([^<]+)</type>.*?<filingDate>([^<]+)</filingDate>.*?<filingHref>([^<]+)</filingHref>.*?</filing>'
            
            for match in re.finditer(filing_pattern, content, re.DOTALL):
                filing_type_found = match.group(1).strip()
                filing_date = match.group(2).strip()
                filing_href = match.group(3).strip()
                
                # Construct full URL
                filing_url = f"https://www.sec.gov{filing_href}"
                
                filings.append({
                    'type': filing_type_found,
                    'date': filing_date,
                    'url': filing_url,
                    'cik': cik
                })
            
            return filings
            
        except Exception as e:
            logger.error(f"Error getting {filing_type} filings for CIK {cik}: {e}")
            return []
    
    def enhance_company_data(self, company_data: Dict, company_name: str) -> Dict:
        """
        Enhance company data with deterministic SEC filing lookup
        
        This method is now the PRIMARY source for SEC data (first choice)
        """
        try:
            # Check if SEC data is already present and complete
            has_cik = company_data.get('identifiers', {}).get('CIK', 'Not available') != 'Not available'
            has_filings = (company_data.get('regulatory_filings', ['Not available']) != ['Not available'] 
                          and company_data.get('regulatory_filings', []) != [])
            has_registration = company_data.get('registration_number', 'Not available') != 'Not available'
            
            if has_cik and has_filings and has_registration:
                logger.info(f"✅ SEC data already complete for {company_name} - CIK: {company_data.get('identifiers', {}).get('CIK')}")
                return company_data
            
            logger.info(f"🔍 PRIMARY SEC lookup for {company_name} - Missing: CIK={not has_cik}, Filings={not has_filings}, Registration={not has_registration}")
            
            # Search for CIK if not found
            cik = None
            if not has_cik:
                cik = self.search_company_cik(company_name)
                if cik:
                    if 'identifiers' not in company_data:
                        company_data['identifiers'] = {}
                    company_data['identifiers']['CIK'] = cik
                    logger.info(f"✅ PRIMARY: Found CIK {cik} for {company_name}")
            else:
                cik = company_data.get('identifiers', {}).get('CIK')
            
            # Get filings if CIK is available
            if cik and not has_filings:
                filings = self.get_company_filings(cik)
                if filings:
                    filing_urls = [f['url'] for f in filings]
                    company_data['regulatory_filings'] = filing_urls
                    logger.info(f"✅ PRIMARY: Found {len(filing_urls)} SEC filings for {company_name}")
                    
                    # Try to extract registration number from 10-K filings
                    if not has_registration:
                        registration_number = self._extract_registration_number_from_filings(filings)
                        if registration_number:
                            company_data['registration_number'] = registration_number
                            logger.info(f"✅ PRIMARY: Found registration number {registration_number} for {company_name}")
            
            # Update confidence level if we enhanced the data
            if cik or (has_cik and not has_filings and cik):
                current_confidence = company_data.get('confidence_level', 'Low')
                if current_confidence == 'Low':
                    company_data['confidence_level'] = 'Medium'
                elif current_confidence == 'Medium' and has_cik and has_filings:
                    company_data['confidence_level'] = 'High'
            
            return company_data
            
        except Exception as e:
            logger.error(f"Error enhancing SEC data for {company_name}: {e}")
            return company_data
    
    def _extract_registration_number_from_filings(self, filings: List[Dict]) -> Optional[str]:
        """Extract registration number from filing metadata or content"""
        try:
            # Look for 10-K filings first
            for filing in filings:
                if filing.get('type', '').startswith('10-K'):
                    # Try to extract from filing URL or content
                    registration_match = re.search(r'(\d{3}-\d{5})', filing.get('url', ''))
                    if registration_match:
                        return registration_match.group(1)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting registration number: {e}")
            return None

# Test function
def test_sec_enhancer():
    """Test the SEC filing enhancer"""
    enhancer = SECFilingEnhancer()
    
    # Test with Diligent
    test_data = {
        'company_name': 'Diligent',
        'legal_name': 'Diligent Corporation',
        'identifiers': {'CIK': 'Not available'},
        'regulatory_filings': ['Not available'],
        'registration_number': 'Not available',
        'confidence_level': 'Medium'
    }
    
    enhanced_data = enhancer.enhance_company_data(test_data, 'Diligent')
    print(json.dumps(enhanced_data, indent=2))

if __name__ == "__main__":
    test_sec_enhancer()

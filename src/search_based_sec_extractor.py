#!/usr/bin/env python3
"""
Search-Based SEC Data Extractor

This module extracts SEC filing information directly from web search results
instead of making separate API calls to SEC databases. This approach is:
- More reliable (no SEC API timeouts)
- Faster (no additional API calls)
- More consistent (uses same search data as other fields)
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class SearchBasedSECExtractor:
    """Extract SEC data directly from search results"""
    
    def __init__(self):
        # Patterns for extracting SEC data from search results
        self.cik_patterns = [
            r'CIK[:\s]*(\d{10})',
            r'CIK[:\s]*(\d{1,10})',
            r'Central Index Key[:\s]*(\d{10})',
            r'edgar/data/(\d+)/',
            r'cik=(\d+)',
            r'CIK:\s*(\d+)'
        ]
        
        self.registration_patterns = [
            r'Commission File Number[:\s]*(\d{3}-\d{5})',
            r'File Number[:\s]*(\d{3}-\d{5})',
            r'Registration[:\s]*(\d{3}-\d{5})',
            r'(\d{3}-\d{5})',  # Generic pattern for XXX-XXXXX format
        ]
        
        self.sec_url_patterns = [
            r'https://www\.sec\.gov/Archives/edgar/data/\d+/\d+/[^"\s]+\.htm?',
            r'https://www\.sec\.gov/ix\?doc=/Archives/edgar/data/\d+/\d+/[^"\s]+\.htm?',
            r'https://edgar\.sec\.gov/[^"\s]+',
        ]
        
        # Executive extraction patterns
        self.executive_patterns = [
            # CEO patterns
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[-–—]\s*(?:Chief Executive Officer|CEO)',
            r'(?:Chief Executive Officer|CEO)[:\s]*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*(?:is|serves as|appointed as)?\s*(?:the\s+)?(?:Chief Executive Officer|CEO)',
            
            # CFO patterns  
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[-–—]\s*(?:Chief Financial Officer|CFO)',
            r'(?:Chief Financial Officer|CFO)[:\s]*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*(?:is|serves as|appointed as)?\s*(?:the\s+)?(?:Chief Financial Officer|CFO)',
            
            # CTO patterns
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[-–—]\s*(?:Chief Technology Officer|CTO)',
            r'(?:Chief Technology Officer|CTO)[:\s]*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            
            # COO patterns
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[-–—]\s*(?:Chief Operating Officer|COO)',
            r'(?:Chief Operating Officer|COO)[:\s]*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        ]
    
    def extract_sec_data_from_search_results(self, search_results: List[Dict], company_name: str) -> Dict:
        """
        Extract SEC data directly from search results
        
        Args:
            search_results: List of search result dictionaries
            company_name: Company name for logging
            
        Returns:
            Dictionary with extracted SEC data
        """
        try:
            logger.info(f"🔍 Extracting SEC data from {len(search_results)} search results for {company_name}")
            
            extracted_data = {
                'cik': None,
                'registration_number': None,
                'sec_filings': [],
                'executives': [],
                'confidence': 'Low'
            }
            
            sec_results = []
            
            # Step 1: Filter and prioritize SEC-related results
            for result in search_results:
                url = result.get('link', '')
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                
                # Check if this is a SEC-related result
                if self._is_sec_related(url, title, snippet):
                    sec_results.append(result)
                    logger.info(f"📋 SEC result found: {title[:50]}...")
            
            logger.info(f"📊 Found {len(sec_results)} SEC-related results")
            
            # Step 2: Extract CIK from SEC results
            extracted_data['cik'] = self._extract_cik_from_results(sec_results)
            
            # Step 3: Extract registration number
            extracted_data['registration_number'] = self._extract_registration_from_results(sec_results)
            
            # Step 4: Extract SEC filing URLs
            extracted_data['sec_filings'] = self._extract_sec_urls_from_results(sec_results)
            
            # Step 5: Extract executive information from all search results
            extracted_data['executives'] = self._extract_executives_from_results(search_results)
            
            # Step 6: Determine confidence level
            extracted_data['confidence'] = self._calculate_confidence(extracted_data)
            
            # Log results
            logger.info(f"✅ SEC extraction completed for {company_name}:")
            logger.info(f"   CIK: {extracted_data['cik']}")
            logger.info(f"   Registration: {extracted_data['registration_number']}")
            logger.info(f"   Filings: {len(extracted_data['sec_filings'])}")
            logger.info(f"   Executives: {len(extracted_data['executives'])}")
            logger.info(f"   Confidence: {extracted_data['confidence']}")
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting SEC data for {company_name}: {e}")
            return {
                'cik': None,
                'registration_number': None,
                'sec_filings': [],
                'executives': [],
                'confidence': 'Low'
            }
    
    def _is_sec_related(self, url: str, title: str, snippet: str) -> bool:
        """Check if a search result is SEC-related"""
        sec_indicators = [
            'sec.gov',
            'edgar.sec.gov',
            'SEC filing',
            'Form 10-K',
            'Form 10-Q',
            'Form 8-K',
            'DEF 14A',
            'Proxy Statement',
            'Commission File Number',
            'CIK',
            'EDGAR'
        ]
        
        text_to_check = f"{url} {title} {snippet}".lower()
        
        for indicator in sec_indicators:
            if indicator.lower() in text_to_check:
                return True
        
        return False
    
    def _extract_cik_from_results(self, sec_results: List[Dict]) -> Optional[str]:
        """Extract CIK from SEC results"""
        for result in sec_results:
            url = result.get('link', '')
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            # Combine all text for pattern matching
            combined_text = f"{url} {title} {snippet}"
            
            # Try each CIK pattern
            for pattern in self.cik_patterns:
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                if matches:
                    # Clean and validate CIK
                    cik = matches[0].strip()
                    if cik.isdigit() and len(cik) <= 10:
                        # Pad with zeros to 10 digits if needed
                        formatted_cik = cik.zfill(10) if len(cik) < 10 else cik
                        logger.info(f"✅ CIK extracted: {formatted_cik} from pattern: {pattern}")
                        return formatted_cik
        
        return None
    
    def _extract_registration_from_results(self, sec_results: List[Dict]) -> Optional[str]:
        """Extract registration number from SEC results"""
        for result in sec_results:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            # Combine text for pattern matching
            combined_text = f"{title} {snippet}"
            
            # Try each registration pattern
            for pattern in self.registration_patterns:
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                if matches:
                    registration = matches[0].strip()
                    # Validate format (XXX-XXXXX)
                    if re.match(r'\d{3}-\d{5}', registration):
                        logger.info(f"✅ Registration number extracted: {registration}")
                        return registration
        
        return None
    
    def _extract_sec_urls_from_results(self, sec_results: List[Dict]) -> List[str]:
        """Extract SEC filing URLs from results"""
        sec_urls = []
        
        for result in sec_results:
            url = result.get('link', '')
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            # Check if the URL itself is a SEC filing
            if self._is_sec_filing_url(url):
                sec_urls.append(url)
                logger.info(f"✅ SEC filing URL found: {url}")
            
            # Look for SEC URLs in snippet text
            combined_text = f"{title} {snippet}"
            for pattern in self.sec_url_patterns:
                matches = re.findall(pattern, combined_text)
                for match in matches:
                    if match not in sec_urls:
                        sec_urls.append(match)
                        logger.info(f"✅ SEC filing URL extracted from text: {match}")
        
        return sec_urls[:5]  # Limit to top 5 filings
    
    def _extract_executives_from_results(self, search_results: List[Dict]) -> List[str]:
        """Extract executive information from search results"""
        executives = []
        found_names = set()
        
        for result in search_results:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            # Combine text for pattern matching
            combined_text = f"{title} {snippet}"
            
            # Try each executive pattern
            for pattern in self.executive_patterns:
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        name = match[0] if match[0] else match[1] if len(match) > 1 else None
                    else:
                        name = match
                    
                    if name and name.strip():
                        name = name.strip()
                        # Determine role based on pattern
                        role = self._determine_executive_role(pattern, combined_text, name)
                        
                        executive_entry = f"{name} - {role}"
                        
                        # Avoid duplicates and filter out invalid names
                        if (name not in found_names and 
                            len(name.split()) >= 2 and 
                            self._is_valid_executive_name(name)):
                            executives.append(executive_entry)
                            found_names.add(name)
                            logger.info(f"✅ Executive extracted: {executive_entry}")
        
        return executives[:10]  # Limit to top 10 executives
    
    def _is_valid_executive_name(self, name: str) -> bool:
        """Check if the extracted name looks like a valid executive name"""
        if not name or len(name.strip()) < 3:
            return False
        
        # Split into words
        words = name.strip().split()
        if len(words) < 2 or len(words) > 4:
            return False
        
        # Check for invalid patterns
        invalid_patterns = [
            r'^rs\b',  # Starts with 'rs' (common extraction error)
            r'^ry\b',  # Starts with 'ry' (common extraction error)
            r'^of\b',  # Starts with 'of'
            r'^and\b', # Starts with 'and'
            r'^the\b', # Starts with 'the'
            r'\b(corporation|company|inc|ltd|llc)\b',  # Contains company words
            r'\b(diligent|intel|microsoft|apple)\b',   # Contains company names
            r'^\w{1,2}\s',  # Very short first word (1-2 chars)
        ]
        
        name_lower = name.lower()
        for pattern in invalid_patterns:
            if re.search(pattern, name_lower):
                return False
        
        # Each word should start with capital letter and be reasonable length
        for word in words:
            if not word[0].isupper() or len(word) < 2:
                return False
            # Check if word contains only letters (no numbers or special chars)
            if not re.match(r'^[A-Za-z]+$', word):
                return False
        
        # Check for common valid name patterns
        # First name + Last name (minimum)
        if len(words) >= 2:
            first_name = words[0]
            last_name = words[-1]
            
            # Names should be reasonable length
            if len(first_name) >= 2 and len(last_name) >= 2:
                return True
        
        return False
    
    def _determine_executive_role(self, pattern: str, text: str, name: str) -> str:
        """Determine executive role based on pattern and context"""
        text_lower = text.lower()
        pattern_lower = pattern.lower()
        
        if 'ceo' in pattern_lower or 'chief executive' in pattern_lower:
            return 'CEO'
        elif 'cfo' in pattern_lower or 'chief financial' in pattern_lower:
            return 'CFO'
        elif 'cto' in pattern_lower or 'chief technology' in pattern_lower:
            return 'CTO'
        elif 'coo' in pattern_lower or 'chief operating' in pattern_lower:
            return 'COO'
        else:
            # Try to determine from context around the name
            name_lower = name.lower()
            context_start = max(0, text_lower.find(name_lower) - 50)
            context_end = min(len(text_lower), text_lower.find(name_lower) + len(name_lower) + 50)
            context = text_lower[context_start:context_end]
            
            if 'ceo' in context or 'chief executive' in context:
                return 'CEO'
            elif 'cfo' in context or 'chief financial' in context:
                return 'CFO'
            elif 'cto' in context or 'chief technology' in context:
                return 'CTO'
            elif 'coo' in context or 'chief operating' in context:
                return 'COO'
            elif 'president' in context:
                return 'President'
            elif 'chairman' in context:
                return 'Chairman'
            else:
                return 'Executive'
    
    def _is_sec_filing_url(self, url: str) -> bool:
        """Check if URL is a direct SEC filing"""
        sec_filing_indicators = [
            'sec.gov/Archives/edgar/data/',
            'sec.gov/ix?doc=/Archives/edgar/data/',
            'edgar.sec.gov'
        ]
        
        for indicator in sec_filing_indicators:
            if indicator in url:
                return True
        
        return False
    
    def _calculate_confidence(self, extracted_data: Dict) -> str:
        """Calculate confidence level based on extracted data"""
        score = 0
        
        if extracted_data['cik']:
            score += 3
        
        if extracted_data['registration_number']:
            score += 2
        
        if extracted_data['sec_filings']:
            score += len(extracted_data['sec_filings'])
        
        if extracted_data['executives']:
            score += len(extracted_data['executives'])
        
        if score >= 7:
            return 'High'
        elif score >= 3:
            return 'Medium'
        else:
            return 'Low'
    
    def enhance_company_data_from_search_no_executives(self, company_data: Dict, search_results: List[Dict], company_name: str) -> Dict:
        """Extract SEC data from search results (excluding executives)"""
        logger.info(f"🔍 Extracting SEC data from {len(search_results)} search results for {company_name} (executives excluded)")
        
        sec_data = self.extract_sec_data_from_search_results(search_results, company_name)
        
        if sec_data['cik']:
            company_data['identifiers'] = company_data.get('identifiers', {})
            company_data['identifiers']['CIK'] = sec_data['cik']
            logger.info(f"✅ SEARCH-BASED: Added CIK {sec_data['cik']} for {company_name}")
        
        if sec_data['registration_number']:
            company_data['registration_number'] = sec_data['registration_number']
            logger.info(f"✅ SEARCH-BASED: Added registration number {sec_data['registration_number']} for {company_name}")
        
        if sec_data['sec_filings']:
            company_data['regulatory_filings'] = sec_data['sec_filings']
            logger.info(f"✅ SEARCH-BASED: Added {len(sec_data['sec_filings'])} SEC filings for {company_name}")
        
        # SKIP executives - they will come from website only
        logger.info(f"🚫 SEARCH-BASED: Skipping {len(sec_data.get('executives', []))} executives - using website-only extraction")
        
        return company_data

    def enhance_company_data_from_search(self, company_data: Dict, search_results: List[Dict], company_name: str) -> Dict:
        """
        Enhance company data with SEC information extracted from search results
        
        This is the main method to use instead of separate SEC API calls
        """
        try:
            # Extract SEC data from search results
            sec_data = self.extract_sec_data_from_search_results(search_results, company_name)
            
            # Update company data with extracted SEC information
            if sec_data['cik'] and (not company_data.get('identifiers', {}).get('CIK') or 
                                   company_data.get('identifiers', {}).get('CIK') == 'Not available'):
                if 'identifiers' not in company_data:
                    company_data['identifiers'] = {}
                company_data['identifiers']['CIK'] = sec_data['cik']
                logger.info(f"✅ SEARCH-BASED: Added CIK {sec_data['cik']} for {company_name}")
            
            if sec_data['registration_number'] and (not company_data.get('registration_number') or 
                                                   company_data.get('registration_number') == 'Not available'):
                company_data['registration_number'] = sec_data['registration_number']
                logger.info(f"✅ SEARCH-BASED: Added registration number {sec_data['registration_number']} for {company_name}")
            
            if sec_data['sec_filings'] and (not company_data.get('regulatory_filings') or 
                                           company_data.get('regulatory_filings') == ['Not available']):
                company_data['regulatory_filings'] = sec_data['sec_filings']
                logger.info(f"✅ SEARCH-BASED: Added {len(sec_data['sec_filings'])} SEC filings for {company_name}")
            
            if sec_data['executives']:
                # Always merge executives, avoiding duplicates
                existing_executives = company_data.get('key_executives', [])
                existing_names = {exec.split(' - ')[0].strip().lower() for exec in existing_executives}
                
                added_count = 0
                for executive in sec_data['executives']:
                    exec_name = executive.split(' - ')[0].strip().lower()
                    if exec_name not in existing_names:
                        existing_executives.append(executive)
                        existing_names.add(exec_name)
                        added_count += 1
                
                company_data['key_executives'] = existing_executives
                logger.info(f"✅ SEARCH-BASED: Added {added_count} new executives, total now: {len(existing_executives)} for {company_name}")
            
            # Update confidence if we found SEC data
            if sec_data['confidence'] == 'High' and company_data.get('confidence_level') != 'High':
                company_data['confidence_level'] = 'High'
            
            return company_data
            
        except Exception as e:
            logger.error(f"❌ Error enhancing company data with search-based SEC extraction: {e}")
            return company_data

# Test function
def test_search_based_extractor():
    """Test the search-based SEC extractor"""
    extractor = SearchBasedSECExtractor()
    
    # Mock search results with SEC data
    mock_results = [
        {
            'title': 'Diligent Corporation - Form 10-K',
            'link': 'https://www.sec.gov/Archives/edgar/data/1433269/000104746916011110/a2227754z10-k.htm',
            'snippet': 'Commission File Number: 001-34756. CIK: 1433269. Diligent Corporation annual report.'
        },
        {
            'title': 'Diligent Corporation Company Info',
            'link': 'https://www.diligent.com/about',
            'snippet': 'Diligent Corporation provides governance software solutions.'
        }
    ]
    
    result = extractor.extract_sec_data_from_search_results(mock_results, 'Diligent')
    print(f"Test result: {result}")

if __name__ == "__main__":
    test_search_based_extractor()

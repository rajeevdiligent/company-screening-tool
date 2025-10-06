#!/usr/bin/env python3
"""
Enhanced Executive Extractor

This module provides comprehensive executive information extraction by:
1. Browsing company websites for leadership pages
2. Analyzing SEC documents for executive data
3. Cross-referencing multiple sources for accuracy
4. Extracting detailed executive profiles with roles and tenure

Usage:
    from enhanced_executive_extractor import EnhancedExecutiveExtractor
    
    extractor = EnhancedExecutiveExtractor()
    executives = extractor.extract_executives(company_name, website_url, sec_filings)
"""

import re
import json
import logging
import requests
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import time
from bs4 import BeautifulSoup
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class ExecutiveProfile:
    """Structured executive information"""
    name: str
    title: str
    role: str  # Standardized role (CEO, CFO, etc.)
    tenure: Optional[str] = None
    background: Optional[str] = None
    source: Optional[str] = None
    confidence: str = "Medium"  # High, Medium, Low

class EnhancedExecutiveExtractor:
    """Enhanced executive information extraction from multiple sources"""
    
    def __init__(self, serper_api_key: str = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Initialize Serper API for targeted executive searches
        self.serper_api_key = serper_api_key
        if not self.serper_api_key:
            import os
            self.serper_api_key = os.getenv('SERPER_API_KEY')
        
        if self.serper_api_key:
            logger.info("Serper API initialized for executive page searches")
        else:
            logger.warning("Serper API key not found - will use basic website crawling")
        
        # Executive role patterns for standardization
        self.role_patterns = {
            'CEO': [
                r'chief executive officer', r'\bCEO\b', r'president and ceo', 
                r'chief executive', r'president & ceo'
            ],
            'CFO': [
                r'chief financial officer', r'\bCFO\b', r'chief finance officer',
                r'finance director', r'financial director'
            ],
            'CTO': [
                r'chief technology officer', r'\bCTO\b', r'chief technical officer',
                r'technology director', r'technical director'
            ],
            'COO': [
                r'chief operating officer', r'\bCOO\b', r'chief operations officer',
                r'operations director', r'operating officer'
            ],
            'CIO': [
                r'chief information officer', r'\bCIO\b', r'chief info officer',
                r'information director', r'it director'
            ],
            'CMO': [
                r'chief marketing officer', r'\bCMO\b', r'marketing director',
                r'chief marketing', r'head of marketing'
            ],
            'CHRO': [
                r'chief human resources officer', r'\bCHRO\b', r'hr director',
                r'human resources director', r'people director', r'chief people officer'
            ],
            'CLO': [
                r'chief legal officer', r'\bCLO\b', r'general counsel', r'legal director',
                r'head of legal', r'chief counsel'
            ],
            'CSO': [
                r'chief strategy officer', r'chief strategy', r'strategy director',
                r'chief security officer', r'chief security', r'security director'
            ],
            'CDO': [
                r'chief data officer', r'\bCDO\b', r'chief data', r'data director',
                r'chief digital officer', r'chief digital', r'digital director'
            ],
            'CRO': [
                r'chief revenue officer', r'\bCRO\b', r'chief revenue', r'revenue director',
                r'chief risk officer', r'chief risk', r'risk director'
            ],
            'CPO': [
                r'chief product officer', r'chief product', r'product director',
                r'chief people officer', r'chief people'
            ],
            'CCO': [
                r'chief compliance officer', r'\bCCO\b', r'chief compliance', r'compliance director',
                r'chief commercial officer', r'chief commercial', r'commercial director',
                r'chief customer officer', r'chief customer', r'customer director'
            ],
            'CAO': [
                r'chief administrative officer', r'\bCAO\b', r'chief administrative', r'administrative director'
            ],
            'Chief Innovation Officer': [
                r'chief innovation officer', r'chief innovation', r'innovation director'
            ],
            'Chief Investment Officer': [
                r'chief investment officer', r'chief investment', r'investment director'
            ],
            'Chief Transformation Officer': [
                r'chief transformation officer', r'chief transformation', r'transformation director'
            ],
            'EVP': [
                r'executive vice president', r'\bEVP\b', r'exec vice president'
            ],
            'SVP': [
                r'senior vice president', r'\bSVP\b', r'sr vice president'
            ],
            'Chairman': [
                r'chairman', r'chairperson', r'chair of the board',
                r'board chairman', r'executive chairman'
            ],
            'Vice Chairman': [
                r'vice chairman', r'vice chairperson', r'vice chair'
            ],
            'President': [
                r'\bpresident\b(?!.*vice)(?!.*ceo)', r'company president'
            ],
            'Founder': [
                r'\bfounder\b', r'co-founder', r'co founder', r'company founder'
            ],
            'Managing Director': [
                r'managing director', r'\bMD\b(?!.*medical)', r'managing dir'
            ],
            'Executive Director': [
                r'executive director', r'exec director'
            ]
        }
        
        # Common leadership page patterns (expanded)
        self.leadership_page_patterns = [
            r'/leadership', r'/team', r'/management', r'/executives',
            r'/about/leadership', r'/company/team', r'/our-team',
            r'/about/management', r'/corporate/leadership', r'/people',
            r'/about/team', r'/company/leadership', r'/company/management',
            r'/corporate/team', r'/our-leadership', r'/our-management',
            r'/about/executives', r'/company/executives', r'/board',
            r'/governance', r'/corporate-governance', r'/investor-relations'
        ]
        
        # Leadership page keywords for detection
        self.leadership_keywords = [
            'leadership', 'team', 'management', 'executives', 'our people',
            'our team', 'our leadership', 'our management', 'board of directors',
            'executive team', 'leadership team', 'management team', 'senior team',
            'c-suite', 'officers', 'key personnel', 'about us', 'governance'
        ]
        
        # SEC document executive extraction patterns
        self.sec_executive_patterns = [
            # DEF 14A patterns (proxy statements)
            r'(?:Mr\.|Ms\.|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+(?:age\s+\d+,?\s+)?(?:has\s+served\s+as\s+)?(?:our\s+)?([^,\n]+?)(?:\s+since|\s+effective|\.|,)',
            
            # 10-K patterns
            r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+serves\s+as\s+(?:our\s+)?([^,\n]+?)(?:\s+and|\.|,)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s+(?:age\s+\d+,?\s+)?(?:is\s+)?(?:our\s+)?([^,\n]+?)(?:\s+of\s+the\s+Company|\.|,)',
            
            # General executive patterns
            r'(?:Mr\.|Ms\.|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+is\s+(?:the\s+)?([^,\n]+?)(?:\s+of\s+(?:the\s+)?Company|\.|,)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+was\s+(?:appointed|named)\s+(?:as\s+)?(?:the\s+)?([^,\n]+?)(?:\s+in|\s+effective|\.|,)'
        ]
    
    async def extract_executives(self, company_name: str, website_url: Optional[str] = None, 
                               sec_filings: Optional[List[str]] = None) -> List[ExecutiveProfile]:
        """
        Extract comprehensive executive information with website as primary source
        
        Strategy:
        1. Extract executives from company website (PRIMARY SOURCE OF TRUTH)
        2. Extract executives from SEC documents (VERIFICATION SOURCE)
        3. Merge and verify, prioritizing website data
        
        Args:
            company_name: Name of the company
            website_url: Company website URL (primary source)
            sec_filings: List of SEC filing URLs (verification source)
            
        Returns:
            List of ExecutiveProfile objects with website data prioritized
        """
        logger.info(f"🔍 Starting website-first executive extraction for {company_name}")
        
        website_executives = []
        sec_executives = []
        
        # PRIMARY SOURCE: Website leadership pages
        if website_url:
            try:
                website_executives = await self._extract_from_website(website_url, company_name)
                logger.info(f"✅ PRIMARY: Found {len(website_executives)} executives from website")
                for exec in website_executives:
                    logger.info(f"   📋 Website: {exec.name} - {exec.role}")
            except Exception as e:
                logger.error(f"❌ Website extraction failed: {e}")
        
        # VERIFICATION SOURCE: SEC documents
        if sec_filings:
            try:
                sec_executives = await self._extract_from_sec_documents(sec_filings, company_name)
                logger.info(f"✅ VERIFICATION: Found {len(sec_executives)} executives from SEC documents")
                for exec in sec_executives:
                    logger.info(f"   📋 SEC: {exec.name} - {exec.role}")
            except Exception as e:
                logger.error(f"❌ SEC document extraction failed: {e}")
        
        # Merge with website as source of truth
        merged_executives = self._merge_with_website_priority(website_executives, sec_executives, company_name)
        
        logger.info(f"🎯 Final result: {len(merged_executives)} verified executives for {company_name}")
        return merged_executives
    
    async def extract_executives_website_only(self, company_name: str, website_url: str, location: str = None) -> List[ExecutiveProfile]:
        """
        Extract executives ONLY from company website using Serper searches
        
        This method uses ONLY website data and ignores SEC documents completely
        If location is 'US', prioritizes global corporate leadership over regional executives
        """
        logger.info(f"🔍 Starting website-ONLY executive extraction for {company_name} (Location: {location or 'Global'})")
        
        try:
            # Use Serper to find executive pages on the company website
            if self.serper_api_key:
                leadership_urls = await self._serper_find_executive_pages(website_url, company_name, location)
            else:
                # Fallback to basic website crawling
                leadership_urls = await self._find_leadership_pages(website_url)
            
            if not leadership_urls:
                logger.warning(f"No leadership pages found for {website_url}")
                return []
            
            # Extract executives from each leadership page
            website_executives = []
            async with aiohttp.ClientSession() as session:
                for url in leadership_urls[:5]:  # Top 5 pages for better coverage
                    try:
                        page_executives = await self._extract_from_leadership_page(session, url, company_name, location)
                        website_executives.extend(page_executives)
                    except Exception as e:
                        logger.error(f"Failed to extract from {url}: {e}")
                        continue
            
            # Filter executives based on location preference
            if location and location.upper() == 'US':
                website_executives = self._filter_for_global_leadership(website_executives, company_name)
            
            # Remove duplicates based on name
            unique_executives = {}
            for exec in website_executives:
                name_key = exec.name.lower().strip()
                if name_key not in unique_executives:
                    exec.source = f"Website: {exec.source}"
                    exec.confidence = "High"
                    unique_executives[name_key] = exec
            
            result = list(unique_executives.values())
            result.sort(key=lambda x: x.name.lower())
            
            location_msg = f" (prioritizing global corporate leaders)" if location and location.upper() == 'US' else ""
            logger.info(f"✅ PRIMARY: Found {len(result)} executives from website ONLY{location_msg}")
            for exec in result:
                logger.info(f"   • {exec.name} - {exec.role}")
            
            return result
            
        except Exception as e:
            logger.error(f"Website-only extraction failed for {website_url}: {e}")
            return []
    
    async def _extract_from_website(self, website_url: str, company_name: str) -> List[ExecutiveProfile]:
        """Extract executives from company website using Serper-targeted searches"""
        executives = []
        
        try:
            # Step 1: Use Serper to find executive pages on the company website
            if self.serper_api_key:
                leadership_urls = await self._serper_find_executive_pages(website_url, company_name)
            else:
                # Fallback to basic website crawling
                leadership_urls = await self._find_leadership_pages(website_url)
            
            if not leadership_urls:
                logger.warning(f"No leadership pages found for {website_url}")
                return executives
            
            # Step 2: Extract executives from each leadership page
            async with aiohttp.ClientSession() as session:
                for url in leadership_urls[:5]:  # Increased to top 5 pages for better coverage
                    try:
                        page_executives = await self._extract_from_leadership_page(session, url, company_name)
                        executives.extend(page_executives)
                    except Exception as e:
                        logger.error(f"Failed to extract from {url}: {e}")
                        continue
            
            return executives
            
        except Exception as e:
            logger.error(f"Website extraction failed for {website_url}: {e}")
            return executives
    
    async def _find_leadership_pages(self, website_url: str) -> List[str]:
        """Find leadership/team pages on the website"""
        leadership_urls = []
        
        try:
            # Get the main page
            response = self.session.get(website_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            base_url = f"{urlparse(website_url).scheme}://{urlparse(website_url).netloc}"
            
            # Look for leadership page links
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '').lower()
                text = link.get_text().lower().strip()
                
                # Skip empty links or non-relevant links
                if not href or href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
                    continue
                
                # Check if this looks like a leadership page
                is_leadership_page = False
                
                # Check URL patterns
                for pattern in self.leadership_page_patterns:
                    if re.search(pattern, href):
                        is_leadership_page = True
                        break
                
                # Check link text for leadership keywords
                if not is_leadership_page:
                    for keyword in self.leadership_keywords:
                        if keyword in text:
                            is_leadership_page = True
                            break
                
                if is_leadership_page:
                    full_url = urljoin(base_url, link['href'])
                    if full_url not in leadership_urls and full_url != website_url:  # Avoid self-reference
                        leadership_urls.append(full_url)
                        logger.info(f"📋 Found leadership page: {full_url} (text: '{text[:50]}...')")
            
            # Also try common leadership page URLs directly
            common_paths = ['/leadership', '/team', '/management', '/executives', '/about/leadership']
            for path in common_paths:
                test_url = urljoin(base_url, path)
                if test_url not in leadership_urls:
                    try:
                        test_response = self.session.head(test_url, timeout=5)
                        if test_response.status_code == 200:
                            leadership_urls.append(test_url)
                            logger.info(f"📋 Found direct leadership page: {test_url}")
                    except:
                        continue
            
            return leadership_urls[:5]  # Limit to top 5 pages
            
        except Exception as e:
            logger.error(f"Failed to find leadership pages: {e}")
            return leadership_urls
    
    async def _serper_find_executive_pages(self, website_url: str, company_name: str, location: str = None) -> List[str]:
        """Use Serper API to find executive/leadership pages on the company website"""
        leadership_urls = []
        
        try:
            from urllib.parse import urlparse
            domain = urlparse(website_url).netloc
            
            # Create search queries based on location preference
            if location and location.upper() == 'US':
                # For US companies, prioritize global corporate leadership
                executive_search_queries = [
                    # Global corporate leadership (highest priority)
                    f'site:{domain} "global leadership"',
                    f'site:{domain} "corporate leadership"',
                    f'site:{domain} "executive leadership"',
                    f'site:{domain} "senior leadership"',
                    f'site:{domain} "company leadership"',
                    f'site:{domain} "board of directors"',
                    f'site:{domain} "executive team"',
                    f'site:{domain} "leadership team"',
                    f'site:{domain} "senior management"',
                    f'site:{domain} "management team"',
                    # Primary leadership pages
                    f'site:{domain} "about us"',
                    f'site:{domain} leadership',
                    f'site:{domain} "our team"',
                    f'site:{domain} executives',
                    # Global CxO-specific searches
                    f'site:{domain} CEO CFO CTO COO "global"',
                    f'site:{domain} "chief executive officer"',
                    f'site:{domain} "chief financial officer"',
                    f'site:{domain} "chief technology officer"',
                    f'site:{domain} "chief operating officer"',
                    f'site:{domain} CIO CMO CHRO CLO "corporate"',
                    f'site:{domain} "chief information officer"',
                    f'site:{domain} "chief marketing officer"',
                    f'site:{domain} CSO CDO CRO CPO "executive"',
                    f'site:{domain} "chief strategy officer"',
                    f'site:{domain} "chief data officer"',
                    f'site:{domain} "chief revenue officer"',
                    f'site:{domain} "chief product officer"',
                    # Worldwide/international focus
                    f'site:{domain} "worldwide" leadership',
                    f'site:{domain} "international" executives',
                    f'site:{domain} "global" management'
                ]
            else:
                # Default comprehensive search for all locations
                executive_search_queries = [
                    # Primary leadership pages
                    f'site:{domain} "about us"',
                    f'site:{domain} leadership',
                    f'site:{domain} "our team"',
                    f'site:{domain} "management team"',
                    f'site:{domain} executives',
                    f'site:{domain} "executive team"',
                    f'site:{domain} "leadership team"',
                    f'site:{domain} "senior management"',
                    f'site:{domain} "board of directors"',
                    f'site:{domain} "company leadership"',
                    # CxO-specific searches
                    f'site:{domain} CEO CFO CTO COO',
                    f'site:{domain} "chief executive" "chief financial"',
                    f'site:{domain} "chief technology" "chief operating"',
                    f'site:{domain} CIO CMO CHRO CLO',
                    f'site:{domain} "chief information" "chief marketing"',
                    f'site:{domain} CSO CDO CRO CPO',
                    f'site:{domain} "chief strategy" "chief data"',
                    f'site:{domain} "chief revenue" "chief product"',
                    # Location-based searches
                    f'site:{domain} "global leadership"',
                    f'site:{domain} "regional leadership"',
                    f'site:{domain} "north america" leadership',
                    f'site:{domain} "europe" leadership',
                    f'site:{domain} "asia" leadership',
                    f'site:{domain} "international" executives',
                    f'site:{domain} "worldwide" management',
                    f'site:{domain} "country" leadership',
                    f'site:{domain} "regional" executives'
                ]
            
            logger.info(f"🔍 Using Serper to find executive pages on {domain}")
            
            for query in executive_search_queries:
                try:
                    results = await self._serper_search(query)
                    
                    for result in results:
                        url = result.get('link', '')
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        
                        # Check if this looks like an executive/leadership page
                        if self._is_executive_page(url, title, snippet):
                            if url not in leadership_urls:
                                # Calculate priority score for sorting
                                priority_score = self._calculate_page_priority(url, title, snippet)
                                leadership_urls.append((url, title, priority_score))
                                logger.info(f"📋 Serper found executive page: {url} (priority: {priority_score})")
                                logger.info(f"   Title: {title[:100]}...")
                    
                    # Limit total pages to avoid overwhelming the system
                    if len(leadership_urls) >= 15:
                        break
                        
                except Exception as e:
                    logger.error(f"Serper search failed for query '{query}': {e}")
                    continue
            
            # Sort by priority score (highest first) and return URLs only
            leadership_urls.sort(key=lambda x: x[2], reverse=True)
            sorted_urls = [url for url, title, score in leadership_urls]
            
            logger.info(f"🎯 Serper found {len(sorted_urls)} executive pages for {company_name}")
            for i, (url, title, score) in enumerate(leadership_urls[:5]):
                logger.info(f"   {i+1}. {url} (score: {score}) - {title[:50]}...")
            
            return sorted_urls[:10]  # Return top 10 URLs by priority
            
        except Exception as e:
            logger.error(f"Serper executive page search failed: {e}")
            return []
    
    async def _serper_search(self, query: str) -> List[Dict]:
        """Perform a Serper API search"""
        try:
            import aiohttp
            
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'q': query,
                'num': 10  # Get top 10 results per query
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post('https://google.serper.dev/search', 
                                      headers=headers, 
                                      json=payload,
                                      timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('organic', [])
                    else:
                        logger.error(f"Serper API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Serper API call failed: {e}")
            return []
    
    def _is_executive_page(self, url: str, title: str, snippet: str) -> bool:
        """Check if a page looks like it contains executive information with priority scoring"""
        # Combine all text for analysis
        combined_text = f"{url} {title} {snippet}".lower()
        
        # High-priority leadership page indicators (actual leadership pages)
        high_priority_indicators = [
            'about us', 'about-us', '/about/', 'leadership', '/leadership/', 
            'our team', 'management team', 'executive team', 'leadership team',
            'executives', '/executives/', 'board of directors', 'senior management'
        ]
        
        # Medium-priority indicators (may contain executive info)
        medium_priority_indicators = [
            'team', 'ceo', 'cfo', 'cto', 'board', 'directors', 'officers', 'senior'
        ]
        
        # Strong exclusions (definitely not leadership pages)
        strong_exclusions = [
            'careers', 'jobs', 'hiring', 'news', 'press', 'blog', 'events',
            'products', 'services', 'contact', 'support', 'legal', 'privacy',
            'solutions', 'resources', 'insights', 'guides', 'podcasts',
            'certification', 'training', 'webinar', 'demo', 'trial'
        ]
        
        # Calculate priority score
        high_priority_score = sum(2 for indicator in high_priority_indicators if indicator in combined_text)
        medium_priority_score = sum(1 for indicator in medium_priority_indicators if indicator in combined_text)
        exclusion_score = sum(1 for exclusion in strong_exclusions if exclusion in combined_text)
        
        total_score = high_priority_score + medium_priority_score - exclusion_score
        
        # Must have positive score and no strong exclusions for high-priority pages
        if high_priority_score > 0 and exclusion_score == 0:
            return True
        elif total_score >= 2 and exclusion_score == 0:
            return True
        else:
            return False
    
    def _calculate_page_priority(self, url: str, title: str, snippet: str) -> int:
        """Calculate priority score for leadership pages"""
        combined_text = f"{url} {title} {snippet}".lower()
        score = 0
        
        # Highest priority: actual leadership/about pages
        if any(indicator in combined_text for indicator in ['about-us', '/about/', 'about us']):
            score += 10
        if any(indicator in combined_text for indicator in ['/leadership/', 'leadership']):
            score += 10
        if any(indicator in combined_text for indicator in ['/team/', 'our team', 'management team']):
            score += 8
        if any(indicator in combined_text for indicator in ['/executives/', 'executive team']):
            score += 8
        
        # Medium priority: pages that likely contain executive info
        if any(indicator in combined_text for indicator in ['board of directors', 'senior management']):
            score += 6
        
        # CxO-specific scoring (higher for multiple CxO mentions)
        cxo_mentions = [
            'ceo', 'chief executive', 'cfo', 'chief financial', 'cto', 'chief technology',
            'coo', 'chief operating', 'cio', 'chief information', 'cmo', 'chief marketing',
            'chro', 'chief human resources', 'clo', 'chief legal', 'cso', 'chief strategy',
            'chief security', 'cdo', 'chief data', 'chief digital', 'cro', 'chief revenue',
            'chief risk', 'cpo', 'chief product', 'chief people', 'cco', 'chief compliance',
            'chief commercial', 'chief customer', 'cao', 'chief administrative'
        ]
        
        cxo_count = sum(1 for mention in cxo_mentions if mention in combined_text)
        if cxo_count >= 3:
            score += 8  # Multiple CxO mentions = high priority
        elif cxo_count >= 2:
            score += 6  # Two CxO mentions = medium-high priority
        elif cxo_count >= 1:
            score += 4  # Single CxO mention = medium priority
        
        # Location-based executive content scoring
        location_indicators = [
            'global leadership', 'regional leadership', 'international executives',
            'worldwide management', 'north america', 'europe', 'asia', 'regional executives',
            'country leadership', 'global team', 'international team'
        ]
        
        location_count = sum(1 for indicator in location_indicators if indicator in combined_text)
        if location_count >= 2:
            score += 6  # Multiple location mentions = high priority for global companies
        elif location_count >= 1:
            score += 3  # Single location mention = medium priority
        
        # Penalty for non-leadership content
        if any(exclusion in combined_text for exclusion in ['blog', 'news', 'resources', 'insights', 'guides']):
            score -= 5
        if any(exclusion in combined_text for exclusion in ['podcast', 'webinar', 'certification', 'training']):
            score -= 3
        
        return max(0, score)  # Ensure non-negative score
    
    async def _extract_from_leadership_page(self, session: aiohttp.ClientSession, 
                                          url: str, company_name: str, location: str = None) -> List[ExecutiveProfile]:
        """Extract executive information from a leadership page"""
        executives = []
        
        try:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return executives
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Look for executive profiles
                page_executives = await self._parse_executive_profiles(soup, url, company_name, location)
                executives.extend(page_executives)
                
                return executives
                
        except Exception as e:
            logger.error(f"Failed to extract from leadership page {url}: {e}")
            return executives
    
    async def _parse_executive_profiles(self, soup: BeautifulSoup, source_url: str, company_name: str, location: str = None) -> List[ExecutiveProfile]:
        """Parse executive profiles from HTML content with enhanced detection"""
        executives = []
        
        # Strategy 1: Look for structured executive sections (leadership page focus)
        executive_selectors = [
            # High-priority leadership page selectors
            (['div', 'section', 'article'], {'class': re.compile(r'leadership|executive|management|team-member|bio|profile', re.I)}),
            (['div', 'section'], {'id': re.compile(r'leadership|executive|management|team|about', re.I)}),
            # Common executive container patterns
            (['div'], {'class': re.compile(r'person|member|staff|employee|leader', re.I)}),
            (['div'], {'class': re.compile(r'card|item|box', re.I)}),
        ]
        
        for tags, attrs in executive_selectors:
            sections = soup.find_all(tags, attrs)
            
            for section in sections:
                try:
                    name = self._extract_name_from_section(section)
                    title = self._extract_title_from_section(section)
                    
                    if name and title and self._is_valid_executive_name(name):
                        role = self._standardize_role(title)
                        background = self._extract_background_from_section(section)
                        
                        executive = ExecutiveProfile(
                            name=name,
                            title=title,
                            role=role,
                            background=background,
                            source=source_url,
                            confidence="High"
                        )
                        executives.append(executive)
                        logger.info(f"✅ Website executive: {name} - {title}")
                        
                except Exception as e:
                    logger.error(f"Failed to parse executive section: {e}")
                    continue
        
        # Strategy 2: Look for executive patterns in page text (always run)
        text_content = soup.get_text()
        text_executives = self._extract_executives_from_text(text_content, source_url)
        executives.extend(text_executives)
        
        # Strategy 3: Look for specific executive title patterns in HTML (always run)
        html_executives = self._extract_executives_from_html(soup, source_url)
        executives.extend(html_executives)
        
        # Strategy 4: Use LLM analysis for comprehensive CxO extraction
        if len(executives) < 3:  # If we found fewer than 3 executives, use LLM
            llm_executives = await self._extract_executives_with_llm(soup, source_url, company_name, location)
            executives.extend(llm_executives)
        
        return executives
    
    def _extract_executives_from_html(self, soup: BeautifulSoup, source_url: str) -> List[ExecutiveProfile]:
        """Extract executives using HTML structure patterns"""
        executives = []
        
        # Look for headings that might contain executive titles
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            heading_text = heading.get_text().strip()
            
            # Check if heading contains executive title
            if self._contains_executive_title(heading_text):
                # Look for name in nearby elements
                name = self._find_name_near_element(heading)
                
                if name and self._is_valid_executive_name(name):
                    role = self._standardize_role(heading_text)
                    
                    executive = ExecutiveProfile(
                        name=name,
                        title=heading_text,
                        role=role,
                        source=source_url,
                        confidence="Medium"
                    )
                    executives.append(executive)
                    logger.info(f"✅ HTML pattern executive: {name} - {heading_text}")
        
        return executives
    
    def _contains_executive_title(self, text: str) -> bool:
        """Check if text contains ANY CxO executive title keywords"""
        text_lower = text.lower()
        executive_titles = [
            # C-Suite executives
            'ceo', 'chief executive', 'cfo', 'chief financial', 'cto', 'chief technology',
            'coo', 'chief operating', 'cio', 'chief information', 'cmo', 'chief marketing',
            'chro', 'chief human resources', 'clo', 'chief legal', 'cso', 'chief strategy',
            'chief security', 'cdo', 'chief data', 'chief digital', 'cro', 'chief revenue',
            'chief risk', 'cpo', 'chief product', 'chief people', 'cco', 'chief compliance',
            'chief commercial', 'chief customer', 'cao', 'chief administrative',
            'chief innovation', 'chief investment', 'chief transformation',
            # Senior positions
            'president', 'chairman', 'vice chairman', 'founder', 'co-founder',
            'managing director', 'executive director', 'executive vice president', 'evp',
            'senior vice president', 'svp', 'vice president', 'vp'
        ]
        
        return any(title in text_lower for title in executive_titles)
    
    def _find_name_near_element(self, element) -> Optional[str]:
        """Find a person's name near a given HTML element"""
        # Check previous sibling
        prev_sibling = element.find_previous_sibling()
        if prev_sibling:
            prev_text = prev_sibling.get_text().strip()
            if self._looks_like_name(prev_text):
                return prev_text
        
        # Check next sibling
        next_sibling = element.find_next_sibling()
        if next_sibling:
            next_text = next_sibling.get_text().strip()
            if self._looks_like_name(next_text):
                return next_text
        
        # Check parent's previous sibling
        parent = element.parent
        if parent:
            parent_prev = parent.find_previous_sibling()
            if parent_prev:
                parent_prev_text = parent_prev.get_text().strip()
                if self._looks_like_name(parent_prev_text):
                    return parent_prev_text
        
        return None
    
    def _is_valid_executive_name(self, name: str) -> bool:
        """Enhanced name validation for executives with stricter filtering"""
        if not name or len(name.strip()) < 5:  # Increased minimum length
            return False
        
        # Split into words
        words = name.strip().split()
        if len(words) < 2 or len(words) > 4:
            return False
        
        # Check for invalid patterns (enhanced)
        invalid_patterns = [
            r'^(mr|ms|dr|prof)\.?\s',  # Titles at start
            r'\b(company|corporation|inc|ltd|llc|group|holdings)\b',  # Company words
            r'\b(diligent|intel|microsoft|apple|google|amazon|business|collaborative)\b',  # Company/generic names
            r'^\w{1,2}\s',  # Very short first word
            r'\d',  # Contains numbers
            r'[^\w\s\-\.]',  # Contains special chars except dash and period
            r'\b(the|more|future|women|business|collaborative)\b',  # Generic words that shouldn't be in names
            r'^(women|business|collaborative|the|more|future)',  # Invalid starting words
            r'(women|business|collaborative|the|more|future)$',  # Invalid ending words
        ]
        
        name_lower = name.lower()
        for pattern in invalid_patterns:
            if re.search(pattern, name_lower):
                logger.debug(f"❌ Invalid name pattern '{pattern}' found in: {name}")
                return False
        
        # Each word should start with capital letter and be reasonable length
        for word in words:
            if not word[0].isupper() or len(word) < 2:
                return False
            # Check if word contains only letters (allow hyphens and periods)
            if not re.match(r'^[A-Za-z\-\.]+$', word):
                return False
            # Reject words that are too generic or business-related
            if word.lower() in ['business', 'collaborative', 'women', 'the', 'more', 'future', 'company', 'corporation']:
                return False
        
        # Must have at least a reasonable first and last name
        if len(words) >= 2:
            first_name = words[0]
            last_name = words[-1]
            if len(first_name) >= 2 and len(last_name) >= 2:
                # Check if it looks like a real person's name
                common_first_names = ['brian', 'john', 'mary', 'david', 'sarah', 'michael', 'jennifer', 'robert', 'lisa', 'william', 'karen', 'richard', 'nancy', 'thomas', 'betty', 'charles', 'helen', 'joseph', 'sandra', 'christopher', 'donna', 'daniel', 'carol', 'matthew', 'ruth', 'anthony', 'sharon', 'mark', 'michelle', 'donald', 'laura', 'steven', 'sarah', 'paul', 'kimberly', 'andrew', 'deborah', 'joshua', 'dorothy', 'kenneth', 'lisa', 'kevin', 'nancy', 'brian', 'karen', 'george', 'betty', 'edward', 'helen', 'ronald', 'sandra', 'timothy', 'donna', 'jason', 'carol', 'jeffrey', 'ruth', 'ryan', 'sharon', 'jacob', 'michelle', 'gary', 'laura', 'nicholas', 'sarah', 'eric', 'kimberly', 'jonathan', 'deborah', 'stephen', 'dorothy', 'larry', 'lisa', 'justin', 'nancy', 'scott', 'karen', 'brandon', 'betty', 'benjamin', 'helen', 'samuel', 'sandra', 'gregory', 'donna', 'alexander', 'carol', 'patrick', 'ruth', 'frank', 'sharon', 'raymond', 'michelle', 'jack', 'laura', 'dennis', 'sarah', 'jerry', 'kimberly', 'tyler', 'deborah', 'aaron', 'dorothy', 'jose', 'lisa', 'henry', 'nancy', 'adam', 'karen', 'douglas', 'betty', 'nathan', 'helen', 'peter', 'sandra', 'zachary', 'donna', 'kyle', 'carol', 'noah', 'ruth', 'alan', 'sharon', 'ethan', 'michelle', 'jeremy', 'laura', 'harold', 'sarah', 'keith', 'kimberly', 'sean', 'deborah', 'austin', 'dorothy', 'carl', 'lisa', 'arthur', 'nancy', 'lawrence', 'karen', 'roger', 'betty', 'joe', 'helen', 'juan', 'sandra', 'wayne', 'donna', 'ralph', 'carol', 'roy', 'ruth', 'eugene', 'sharon', 'louis', 'michelle', 'philip', 'laura', 'bobby', 'sarah', 'edie', 'meghan', 'vaibhav']
                
                # If first name is in common names list, it's likely valid
                if first_name.lower() in common_first_names:
                    return True
                
                # Otherwise, apply stricter validation
                return len(first_name) >= 3 and len(last_name) >= 3
        
        return False
    
    async def _extract_executives_with_llm(self, soup: BeautifulSoup, source_url: str, company_name: str, location: str = None) -> List[ExecutiveProfile]:
        """Use LLM to extract executives from page content with location awareness"""
        try:
            # Get clean text content
            text_content = soup.get_text()
            
            # Clean and truncate content for LLM analysis
            clean_content = ' '.join(text_content.split())[:8000]  # Limit to 8000 chars
            
            # Create LLM prompt for executive extraction based on location
            if location and location.upper() == 'US':
                # US-focused prompt for global corporate leadership
                prompt = f"""
                Analyze the following webpage content from {company_name} ({source_url}) and extract GLOBAL CORPORATE LEADERS and C-suite executives.

                PRIORITY FOCUS FOR US COMPANIES:
                1. Extract ONLY global corporate leaders and C-suite executives (not regional managers)
                2. HIGHEST PRIORITY: CEO, CFO, CTO, COO, President, Chairman, Vice Chairman
                3. SECONDARY PRIORITY: CIO, CMO, CHRO, CLO, CSO, CDO, CRO, CPO, CCO, CAO
                4. INCLUDE: Founder, Co-Founder, Executive Vice President (EVP), Senior Vice President (SVP)
                5. EXCLUDE: Regional managers, country managers, division heads unless they are C-level
                6. EXCLUDE: Titles with specific regions like "President, Canada" or "VP, Europe" unless they are also global roles
                7. PRIORITIZE: Corporate headquarters leadership over regional/local leadership
                8. Return ONLY executives you are confident about with global/corporate scope

                Content to analyze:
                {clean_content}

                Please extract GLOBAL CORPORATE executives in this exact JSON format:
                {{
                    "executives": [
                        {{
                            "name": "Full Name",
                            "title": "Complete Corporate Title",
                            "scope": "Global/Corporate",
                            "confidence": "High/Medium/Low"
                        }}
                    ]
                }}
                """
            else:
                # Default comprehensive prompt for non-US companies
                prompt = f"""
                Analyze the following webpage content from {company_name} ({source_url}) and extract ALL C-level executives (CxO) and senior leadership positions.

                IMPORTANT INSTRUCTIONS:
                1. Extract ONLY real people with actual names (not generic titles)
                2. Focus on C-level executives: CEO, CFO, CTO, COO, CIO, CMO, CHRO, CLO, CSO, CDO, CRO, CPO, CCO, CAO, etc.
                3. Also include: President, Chairman, Vice Chairman, Founder, Co-Founder, Managing Director, Executive Director, EVP, SVP
                4. Include location/region information if mentioned (e.g., "President, North America", "CEO, Europe", "Managing Director, Asia")
                5. Return ONLY executives you are confident about
                6. Format: Name - Title (Location if available)

                Content to analyze:
                {clean_content}

                Please extract executives in this exact JSON format:
                {{
                    "executives": [
                        {{
                            "name": "Full Name",
                            "title": "Complete Title",
                            "location": "Region/Location if mentioned",
                            "confidence": "High/Medium/Low"
                        }}
                    ]
                }}
                """
            
            # Use AWS Bedrock Nova Pro for analysis
            import boto3
            import json
            
            # Use the same session as the main application
            session = boto3.Session(profile_name='diligent')
            bedrock = session.client('bedrock-runtime', region_name='us-east-1')
            
            response = bedrock.invoke_model(
                modelId='amazon.nova-pro-v1:0',
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": prompt}]
                        }
                    ],
                    "inferenceConfig": {
                        "max_new_tokens": 2000,
                        "temperature": 0.1
                    }
                })
            )
            
            response_body = json.loads(response['body'].read())
            llm_response = response_body['output']['message']['content'][0]['text']
            
            # Parse LLM response
            executives = []
            try:
                # Extract JSON from response
                json_start = llm_response.find('{')
                json_end = llm_response.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = llm_response[json_start:json_end]
                    parsed_response = json.loads(json_str)
                    
                    for exec_data in parsed_response.get('executives', []):
                        name = exec_data.get('name', '').strip()
                        title = exec_data.get('title', '').strip()
                        confidence = exec_data.get('confidence', 'Medium')
                        
                        # Handle different JSON formats for US vs non-US companies
                        if location and location.upper() == 'US':
                            # US format uses 'scope' field
                            scope = exec_data.get('scope', '').strip()
                            full_title = f"{title} ({scope})" if scope else title
                            location_info = scope
                        else:
                            # Non-US format uses 'location' field
                            location_info = exec_data.get('location', '').strip()
                            full_title = f"{title} ({location_info})" if location_info else title
                        
                        if name and title and self._is_valid_executive_name(name):
                            role = self._standardize_role(title)
                            executive = ExecutiveProfile(
                                name=name,
                                title=full_title,
                                role=role,
                                source=source_url,
                                confidence=confidence
                            )
                            executives.append(executive)
                            
                            if location and location.upper() == 'US':
                                logger.info(f"✅ LLM GLOBAL executive: {name} - {full_title}")
                            else:
                                logger.info(f"✅ LLM executive: {name} - {full_title}")
            
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response as JSON: {e}")
                # Fallback: try to extract from text
                executives = self._extract_executives_from_llm_text(llm_response, source_url)
            
            logger.info(f"🤖 LLM extracted {len(executives)} executives from {source_url}")
            return executives
            
        except Exception as e:
            logger.error(f"LLM executive extraction failed for {source_url}: {e}")
            return []
    
    def _extract_executives_from_llm_text(self, llm_text: str, source_url: str) -> List[ExecutiveProfile]:
        """Fallback method to extract executives from LLM text response"""
        executives = []
        lines = llm_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('*'):
                continue
                
            # Look for patterns like "Name - Title" or "Name: Title"
            for separator in [' - ', ': ', ' – ', ' — ']:
                if separator in line:
                    parts = line.split(separator, 1)
                    if len(parts) == 2:
                        name = parts[0].strip()
                        title = parts[1].strip()
                        
                        # Clean up formatting
                        name = name.replace('**', '').replace('*', '').strip()
                        title = title.replace('**', '').replace('*', '').strip()
                        
                        if self._is_valid_executive_name(name) and self._contains_executive_title(title):
                            role = self._standardize_role(title)
                            executive = ExecutiveProfile(
                                name=name,
                                title=title,
                                role=role,
                                source=source_url,
                                confidence="Medium"
                            )
                            executives.append(executive)
                            logger.info(f"✅ LLM text executive: {name} - {title}")
                            break
        
        return executives
    
    def _filter_for_global_leadership(self, executives: List[ExecutiveProfile], company_name: str) -> List[ExecutiveProfile]:
        """Filter executives to prioritize global corporate leaders over regional/local executives"""
        if not executives:
            return executives
        
        logger.info(f"🌍 Filtering for global corporate leadership for {company_name}")
        
        # Define global leadership indicators
        global_indicators = [
            'global', 'worldwide', 'international', 'corporate', 'chief', 'president', 
            'chairman', 'ceo', 'cfo', 'cto', 'coo', 'cio', 'cmo', 'chro', 'clo', 
            'cso', 'cdo', 'cro', 'cpo', 'cco', 'cao', 'founder', 'co-founder'
        ]
        
        # Regional/local indicators to deprioritize
        regional_indicators = [
            'canada', 'canadian', 'north america', 'americas', 'europe', 'european',
            'asia', 'asian', 'pacific', 'regional', 'country', 'local', 'division',
            'reno', 'nevada', 'toronto', 'london', 'singapore', 'tokyo', 'sydney'
        ]
        
        # Score executives based on global vs regional indicators
        scored_executives = []
        for exec in executives:
            title_lower = exec.title.lower()
            name_lower = exec.name.lower()
            combined_text = f"{title_lower} {name_lower}"
            
            global_score = sum(1 for indicator in global_indicators if indicator in combined_text)
            regional_score = sum(1 for indicator in regional_indicators if indicator in combined_text)
            
            # Calculate priority score (higher = more global)
            priority_score = global_score - (regional_score * 0.5)
            
            # Boost score for C-level executives
            if any(title in title_lower for title in ['chief', 'ceo', 'cfo', 'cto', 'coo', 'president', 'chairman']):
                priority_score += 2
            
            # Penalize obvious regional roles
            if any(region in combined_text for region in ['canada', 'reno', 'asia', 'europe']):
                priority_score -= 1
            
            scored_executives.append((exec, priority_score))
        
        # Sort by priority score (highest first) and take top executives
        scored_executives.sort(key=lambda x: x[1], reverse=True)
        
        # Filter to keep only high-priority global executives
        filtered_executives = []
        for exec, score in scored_executives:
            if score >= 1.0:  # Only keep executives with positive global score
                filtered_executives.append(exec)
            elif len(filtered_executives) < 5:  # Keep at least 5 executives
                filtered_executives.append(exec)
        
        logger.info(f"🎯 Filtered to {len(filtered_executives)} global corporate leaders from {len(executives)} total executives")
        for exec in filtered_executives[:10]:  # Log top 10
            logger.info(f"   • {exec.name} - {exec.title}")
        
        return filtered_executives
    
    def format_executives_for_output(self, executives: List[ExecutiveProfile]) -> List[str]:
        """Format executive profiles for JSON output"""
        formatted = []
        for exec in executives:
            if hasattr(exec, 'name') and hasattr(exec, 'title'):
                # Clean up name and title formatting
                name = exec.name.strip()
                title = exec.title.strip()
                
                # Remove excessive whitespace and line breaks
                name = ' '.join(name.split())
                title = ' '.join(title.split())
                
                if name and title:
                    formatted.append(f"{name} - {title}")
        
        return formatted
    
    def _extract_name_from_section(self, section) -> Optional[str]:
        """Extract executive name from HTML section"""
        # Look for name in various elements
        name_selectors = ['h1', 'h2', 'h3', 'h4', '.name', '.executive-name', '.person-name']
        
        for selector in name_selectors:
            elements = section.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if self._looks_like_name(text):
                    return text
        
        return None
    
    def _extract_title_from_section(self, section) -> Optional[str]:
        """Extract executive title from HTML section"""
        # Look for title in various elements
        title_selectors = ['.title', '.position', '.role', '.job-title', 'p', 'span']
        
        for selector in title_selectors:
            elements = section.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if self._looks_like_title(text):
                    return text
        
        return None
    
    def _extract_background_from_section(self, section) -> Optional[str]:
        """Extract executive background/bio from HTML section"""
        # Look for longer text content that might be a bio
        paragraphs = section.find_all('p')
        
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 50:  # Likely a bio if longer than 50 chars
                return text[:500]  # Limit to 500 chars
        
        return None
    
    def _looks_like_name(self, text: str) -> bool:
        """Check if text looks like a person's name"""
        if not text or len(text) > 50:
            return False
        
        # Should have 2-4 words, each starting with capital letter
        words = text.split()
        if len(words) < 2 or len(words) > 4:
            return False
        
        return all(word[0].isupper() for word in words if word)
    
    def _looks_like_title(self, text: str) -> bool:
        """Check if text looks like a job title"""
        if not text or len(text) > 100:
            return False
        
        title_keywords = [
            'chief', 'officer', 'director', 'president', 'vice', 'senior',
            'head', 'manager', 'lead', 'executive', 'chairman', 'founder'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in title_keywords)
    
    def _extract_executives_from_text(self, text: str, source_url: str) -> List[ExecutiveProfile]:
        """Extract executives from plain text using enhanced patterns"""
        executives = []
        
        # Comprehensive patterns for ALL CxO executive extraction
        cxo_titles = r'(?:Chief Executive Officer|CEO|Chief Financial Officer|CFO|Chief Technology Officer|CTO|Chief Operating Officer|COO|Chief Information Officer|CIO|Chief Marketing Officer|CMO|Chief Human Resources Officer|CHRO|Chief Legal Officer|CLO|Chief Strategy Officer|CSO|Chief Data Officer|CDO|Chief Security Officer|CSO|Chief Revenue Officer|CRO|Chief Product Officer|CPO|Chief Innovation Officer|Chief Compliance Officer|CCO|Chief Risk Officer|CRO|Chief Administrative Officer|CAO|Chief Investment Officer|Chief Commercial Officer|Chief Customer Officer|Chief Digital Officer|Chief People Officer|CPO|Chief Transformation Officer|President|Chairman|Vice Chairman|Founder|Co-Founder|Managing Director|Executive Director|Executive Vice President|EVP|Senior Vice President|SVP)'
        
        patterns = [
            # Name - Title (with various separators)
            rf'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){{1,3}})\s*[-–—,:\s]+\s*({cxo_titles})',
            # Title: Name or Title - Name
            rf'({cxo_titles})[:\s,-]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){{1,3}})',
            # Name (Title) or Name [Title]
            rf'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){{1,3}})\s*[\(\[]\s*({cxo_titles})\s*[\)\]]',
            # Name serves as Title / Name is the Title
            rf'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){{1,3}})\s+(?:serves as|is the|is our|acts as)\s+({cxo_titles})',
            # Name, Title format
            rf'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){{1,3}}),\s*({cxo_titles})',
            # Title Name format (simple)
            rf'({cxo_titles})\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){{1,3}})',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                groups = match.groups()
                if len(groups) == 2:
                    # Determine which group is name and which is title
                    if any(title_word.lower() in groups[0].lower() for title_word in ['ceo', 'cfo', 'cto', 'coo', 'president', 'chairman', 'founder', 'director']):
                        title, name = groups
                    else:
                        name, title = groups
                    
                    name = name.strip()
                    title = title.strip()
                    
                    if self._is_valid_executive_name(name) and len(name) > 5:
                        role = self._standardize_role(title)
                        executive = ExecutiveProfile(
                            name=name,
                            title=title,
                            role=role,
                            source=source_url,
                            confidence="Medium"
                        )
                        executives.append(executive)
                        logger.info(f"✅ Text pattern executive: {name} - {title}")
        
        return executives
    
    async def _extract_from_sec_documents(self, sec_filings: List[str], 
                                        company_name: str) -> List[ExecutiveProfile]:
        """Extract executives from SEC documents"""
        executives = []
        
        async with aiohttp.ClientSession() as session:
            for filing_url in sec_filings[:3]:  # Limit to top 3 filings
                try:
                    doc_executives = await self._extract_from_sec_document(session, filing_url, company_name)
                    executives.extend(doc_executives)
                except Exception as e:
                    logger.error(f"Failed to extract from SEC document {filing_url}: {e}")
                    continue
        
        return executives
    
    async def _extract_from_sec_document(self, session: aiohttp.ClientSession, 
                                       filing_url: str, company_name: str) -> List[ExecutiveProfile]:
        """Extract executives from a single SEC document"""
        executives = []
        
        try:
            async with session.get(filing_url, timeout=15) as response:
                if response.status != 200:
                    return executives
                
                content = await response.text()
                
                # Clean up HTML if present
                if '<html' in content.lower():
                    soup = BeautifulSoup(content, 'html.parser')
                    content = soup.get_text()
                
                # Extract executives using SEC-specific patterns
                for pattern in self.sec_executive_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                    
                    for match in matches:
                        if isinstance(match, tuple) and len(match) >= 2:
                            name = match[0].strip()
                            title = match[1].strip()
                            
                            if self._looks_like_name(name) and self._looks_like_title(title):
                                role = self._standardize_role(title)
                                
                                executive = ExecutiveProfile(
                                    name=name,
                                    title=title,
                                    role=role,
                                    source=filing_url,
                                    confidence="High"  # SEC documents are highly reliable
                                )
                                executives.append(executive)
                                logger.info(f"✅ SEC executive: {name} - {title}")
                
                return executives
                
        except Exception as e:
            logger.error(f"Failed to extract from SEC document {filing_url}: {e}")
            return executives
    
    def _standardize_role(self, title: str) -> str:
        """Standardize executive role based on title"""
        title_lower = title.lower()
        
        for role, patterns in self.role_patterns.items():
            for pattern in patterns:
                if re.search(pattern, title_lower):
                    return role
        
        # Default to the original title if no standard role found
        return title
    
    def _merge_with_website_priority(self, website_executives: List[ExecutiveProfile], 
                                   sec_executives: List[ExecutiveProfile], company_name: str) -> List[ExecutiveProfile]:
        """
        Merge executives with website as primary source of truth
        
        Priority Logic:
        1. Website data is ALWAYS preferred for name, title, and role
        2. SEC data is used for verification and additional context
        3. If executive exists in both sources, website data takes precedence
        4. If executive only exists in SEC, include with verification flag
        """
        merged = {}
        
        # Step 1: Add all website executives as primary source of truth
        for exec in website_executives:
            name_key = exec.name.lower().strip()
            exec.confidence = "High"  # Website is source of truth
            exec.source = f"Website: {exec.source}"
            merged[name_key] = exec
            logger.info(f"🌐 PRIMARY: {exec.name} - {exec.role} (from website)")
        
        # Step 2: Process SEC executives for verification and additional data
        for sec_exec in sec_executives:
            name_key = sec_exec.name.lower().strip()
            
            if name_key in merged:
                # Executive exists in website data - use for verification
                website_exec = merged[name_key]
                
                # Check if roles match for verification
                if self._roles_match(website_exec.role, sec_exec.role):
                    website_exec.confidence = "High"  # Verified by SEC
                    website_exec.source += f" | Verified by SEC: {sec_exec.source}"
                    logger.info(f"✅ VERIFIED: {website_exec.name} - {website_exec.role} (website + SEC match)")
                else:
                    # Role mismatch - note the discrepancy but keep website data
                    website_exec.source += f" | SEC shows different role: {sec_exec.role}"
                    logger.warning(f"⚠️ MISMATCH: {website_exec.name} - Website: {website_exec.role} vs SEC: {sec_exec.role}")
                
                # Add SEC background info if website doesn't have it
                if not website_exec.background and sec_exec.background:
                    website_exec.background = sec_exec.background
                
            else:
                # Executive only found in SEC - include with lower confidence
                sec_exec.confidence = "Medium"  # Not verified by website
                sec_exec.source = f"SEC only: {sec_exec.source}"
                merged[name_key] = sec_exec
                logger.info(f"📋 SEC-ONLY: {sec_exec.name} - {sec_exec.role} (not found on website)")
        
        # Step 3: Sort by priority (website-verified first, then SEC-only)
        result = list(merged.values())
        result.sort(key=lambda x: (
            0 if "Website:" in x.source else 1,  # Website first
            0 if x.confidence == "High" else 1,   # High confidence first
            x.name.lower()                        # Alphabetical
        ))
        
        logger.info(f"🎯 MERGE COMPLETE: {len(result)} executives for {company_name}")
        return result
    
    def _roles_match(self, website_role: str, sec_role: str) -> bool:
        """Check if roles from website and SEC are equivalent"""
        # Normalize roles for comparison
        website_normalized = website_role.lower().strip()
        sec_normalized = sec_role.lower().strip()
        
        # Direct match
        if website_normalized == sec_normalized:
            return True
        
        # Check for common role equivalencies
        role_equivalencies = {
            'ceo': ['chief executive officer', 'president and ceo', 'chief executive'],
            'cfo': ['chief financial officer', 'chief finance officer'],
            'cto': ['chief technology officer', 'chief technical officer'],
            'coo': ['chief operating officer', 'chief operations officer'],
            'president': ['president and ceo', 'company president'],
            'chairman': ['chairman of the board', 'board chairman', 'executive chairman']
        }
        
        for standard_role, variations in role_equivalencies.items():
            if (standard_role in website_normalized or any(var in website_normalized for var in variations)) and \
               (standard_role in sec_normalized or any(var in sec_normalized for var in variations)):
                return True
        
        return False
    
    def _merge_executive_profiles(self, executives: List[ExecutiveProfile]) -> List[ExecutiveProfile]:
        """Legacy merge method - kept for backward compatibility"""
        merged = {}
        
        for exec in executives:
            # Use name as key for deduplication
            name_key = exec.name.lower().strip()
            
            if name_key not in merged:
                merged[name_key] = exec
            else:
                # Merge with existing profile, preferring higher confidence
                existing = merged[name_key]
                
                # Prefer higher confidence source
                if exec.confidence == "High" and existing.confidence != "High":
                    merged[name_key] = exec
                elif exec.confidence == existing.confidence:
                    # If same confidence, prefer website source
                    if "website" in exec.source.lower() and "website" not in existing.source.lower():
                        merged[name_key] = exec
                    # Otherwise, merge information
                    else:
                        if not existing.background and exec.background:
                            existing.background = exec.background
                        if not existing.tenure and exec.tenure:
                            existing.tenure = exec.tenure
        
        return list(merged.values())
    
    def format_executives_for_output(self, executives: List[ExecutiveProfile]) -> List[str]:
        """Format executives for the main search output"""
        formatted = []
        
        # Sort by role importance
        role_priority = {
            'CEO': 1, 'President': 2, 'CFO': 3, 'COO': 4, 'CTO': 5,
            'CMO': 6, 'CHRO': 7, 'General Counsel': 8, 'Chairman': 9
        }
        
        executives.sort(key=lambda x: role_priority.get(x.role, 99))
        
        for exec in executives:
            if exec.role in role_priority:
                formatted.append(f"{exec.name} - {exec.role}")
            else:
                formatted.append(f"{exec.name} - {exec.title}")
        
        return formatted

# Test function
async def test_enhanced_executive_extractor():
    """Test the enhanced executive extractor"""
    extractor = EnhancedExecutiveExtractor()
    
    # Test with Diligent
    executives = await extractor.extract_executives(
        company_name="Diligent Corporation",
        website_url="https://www.diligent.com",
        sec_filings=["https://www.sec.gov/Archives/edgar/data/1433269/000104746916011110/a2227754z10-k.htm"]
    )
    
    print(f"Found {len(executives)} executives:")
    for exec in executives:
        print(f"  • {exec.name} - {exec.role} ({exec.confidence} confidence)")

if __name__ == "__main__":
    asyncio.run(test_enhanced_executive_extractor())

#!/usr/bin/env python3
"""
Test script to demonstrate the expected JSON output format
This creates a sample output based on the image provided
"""

import json
from datetime import datetime
from company_research import CompanyInfo

def create_sample_google_data():
    """Create sample Google data matching the image format"""
    
    # Create CompanyInfo object with all fields from the image
    google_info = CompanyInfo(
        company_name="Google",
        legal_name="Google LLC",
        registration_number="3582691",
        incorporation_date="2002-10-22",
        incorporation_country="United States",
        jurisdiction="Delaware, United States",
        business_type="Limited Liability Company",
        industry="Technology, Internet Services",
        headquarters="C/O CORPORATION SERVICE COMPANY, 251 LITTLE FALLS DRIVE, WILMINGTON, 19808, United States of America",
        website="google.com",
        description="Google LLC, a subsidiary of Alphabet Inc, is a provider of search and advertising services on the internet. The company offers a wide range of products and services including search, advertising, operating systems, platforms, enterprise and hardware products.",
        products_services="Search engine, online advertising, cloud computing, software, hardware, artificial intelligence",
        alternate_names=["Google Inc."],
        identifiers={
            "LEI": "7ZW8QJWVPR4P1JKQY45",
            "DUNS": "",
            "EIN": "",
            "CIK": ""
        },
        key_executives=[
            "Sundar Pichai - CEO",
            "Ruth Porat - CFO"
        ],
        subsidiaries=[
            "YouTube",
            "Waymo",
            "DeepMind"
        ],
        parent_company="Alphabet Inc.",
        stock_symbol="GOOGL",
        market_cap="$1.7 trillion",
        annual_revenue="$350 billion (2024)",
        employees="183323",
        founded_year="1998",
        regulatory_filings=[
            "Form 10-K 2023",
            "Form 10-Q Q3 2024"
        ],
        sources=[
            "https://sec.gov/edgar/browse/?CIK=1652044",
            "https://abc.xyz/investor/",
            "https://www.google.com/about/"
        ]
    )
    
    return google_info

def main():
    """Generate and save sample JSON output"""
    
    print("Creating sample Google company data matching the image format...")
    
    # Create sample data
    google_data = create_sample_google_data()
    
    # Convert to dictionary for JSON serialization
    from dataclasses import asdict
    google_dict = asdict(google_data)
    
    # Save to JSON file
    output_file = "sample_google_research.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(google_dict, f, indent=2, ensure_ascii=False)
    
    print(f"Sample JSON output saved to: {output_file}")
    
    # Display formatted output matching the image structure
    print(f"\n{'='*80}")
    print("ENTITY OVERVIEW")
    print(f"{'='*80}")
    
    print(f"\nLegal Name: {google_data.legal_name}")
    print(f"Incorporation Country: {google_data.incorporation_country}")
    print(f"Incorporation Date: {google_data.incorporation_date}")
    print(f"Registration Number: {google_data.registration_number}")
    print(f"Address: {google_data.headquarters}")
    
    if google_data.alternate_names:
        print(f"Alternate Names: {', '.join(google_data.alternate_names)}")
    
    if google_data.identifiers and any(google_data.identifiers.values()):
        identifiers = [f"{k}: {v}" for k, v in google_data.identifiers.items() if v]
        print(f"Identifiers: {', '.join(identifiers)}")
    
    print(f"\n{'='*80}")
    print("COMPANY PROFILE")
    print(f"{'='*80}")
    
    print(f"\nDescription: {google_data.description}")
    print(f"Industry: {google_data.industry}")
    print(f"Products/Services: {google_data.products_services}")
    print(f"Employees: {google_data.employees}")
    print(f"Annual Revenue: {google_data.annual_revenue}")
    print(f"Website: {google_data.website}")
    
    print(f"\nJSON structure includes all fields from the image:")
    print("✓ Legal Name")
    print("✓ Incorporation Country") 
    print("✓ Incorporation Date")
    print("✓ Registration Number")
    print("✓ Address (Headquarters)")
    print("✓ Alternate Names")
    print("✓ Identifiers (LEI, DUNS, etc.)")
    print("✓ Description")
    print("✓ Industry")
    print("✓ Products/Services")
    print("✓ Employees")
    print("✓ Annual Revenue")
    print("✓ Website")
    
    print(f"\nFull JSON data structure saved to: {output_file}")

if __name__ == "__main__":
    main()

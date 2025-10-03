# Company Research Tool

A comprehensive Python tool for extracting detailed company information using SERPER API for web search and AWS Nova Pro LLM for intelligent analysis.

## Features

- **Comprehensive Company Research**: Extracts official company information from reliable sources
- **Multiple Search Strategies**: Handles company name variations, abbreviations, and synonyms
- **AWS Nova Pro Integration**: Uses advanced LLM for intelligent data analysis
- **Reliable Sources Only**: Focuses on government registries, SEC filings, annual reports, and official databases
- **Structured Output**: Returns data in JSON format for easy integration

## Setup

### 1. Environment Setup

Create a `.env` file in the project directory:

```bash
# Environment Configuration
SERPER_API_KEY=your_serper_api_key_here

# AWS Configuration
AWS_PROFILE=diligent
AWS_REGION=us-east-1

# Company Research Configuration
MAX_SEARCH_RESULTS=10
SEARCH_TIMEOUT=30
```

### 2. AWS Configuration

Ensure your AWS credentials are configured for the "diligent" profile:

```bash
aws configure --profile diligent
```

Or add to `~/.aws/credentials`:

```ini
[diligent]
aws_access_key_id = your_access_key
aws_secret_access_key = your_secret_key
region = us-east-1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python company_research.py --company "Google"
```

### Advanced Usage

```bash
# Specify custom output file
python company_research.py --company "Microsoft" --output "microsoft_research.json"

# Enable verbose logging
python company_research.py --company "Apple" --verbose
```

### Programmatic Usage

```python
import asyncio
from company_research import CompanyResearcher

async def research_company():
    researcher = CompanyResearcher()
    company_info = await researcher.research_company("Tesla")
    researcher.save_results(company_info)

asyncio.run(research_company())
```

## Output Format

The tool generates comprehensive company information in JSON format:

```json
{
  "company_name": "Google",
  "official_name": "Alphabet Inc.",
  "registration_number": "C2943805",
  "incorporation_date": "2015-07-23",
  "jurisdiction": "Delaware, USA",
  "business_type": "Corporation",
  "industry": "Technology/Internet Services",
  "headquarters": "1600 Amphitheatre Parkway, Mountain View, CA 94043",
  "website": "https://abc.xyz",
  "description": "Multinational technology conglomerate",
  "key_executives": ["Sundar Pichai - CEO", "Ruth Porat - CFO"],
  "subsidiaries": ["Google LLC", "YouTube", "Waymo"],
  "parent_company": "",
  "stock_symbol": "GOOGL",
  "market_cap": "$1.7 trillion",
  "revenue": "$307.4 billion (2023)",
  "employees": "182,502",
  "founded_year": "1998",
  "regulatory_filings": ["Form 10-K 2023", "Form 10-Q Q3 2024"],
  "sources": ["https://sec.gov/...", "https://abc.xyz/..."],
  "last_updated": "2024-01-15T10:30:00"
}
```

## Data Sources

The tool prioritizes official and reliable sources:

- **Government Registries**: SEC filings, state incorporation records
- **Annual Reports**: Official company annual and quarterly reports
- **Regulatory Filings**: 10-K, 10-Q, 8-K forms and international equivalents
- **Corporate Websites**: Official press releases and investor relations
- **Trusted Databases**: Bloomberg, Reuters, official stock exchanges

## Company Name Variations

The tool automatically handles:

- **Legal Suffixes**: Inc., Corp., LLC, Ltd., etc.
- **Abbreviations**: IBM for International Business Machines
- **Local Spellings**: Regional name variations
- **Synonyms**: Common alternative names
- **Historical Names**: Former company names

## Error Handling

- Comprehensive logging to `company_research.log`
- Graceful handling of API failures
- Source verification and confidence scoring
- Timeout protection for long-running searches

## API Requirements

### SERPER API
- Sign up at [serper.dev](https://serper.dev)
- Get your API key
- Add to `.env` file as `SERPER_API_KEY`

### AWS Nova Pro
- Requires AWS account with Bedrock access
- Nova Pro model must be enabled in your region
- Proper IAM permissions for Bedrock runtime

## Troubleshooting

### Common Issues

1. **AWS Credentials Error**
   ```bash
   aws configure --profile diligent
   ```

2. **SERPER API Key Missing**
   - Check `.env` file exists and contains `SERPER_API_KEY`

3. **Nova Pro Access Denied**
   - Ensure Bedrock access is enabled in AWS console
   - Check IAM permissions for bedrock-runtime

4. **Rate Limiting**
   - Tool includes automatic delays between requests
   - Reduce `MAX_SEARCH_RESULTS` in `.env` if needed

### Logging

Enable verbose logging for debugging:

```bash
python company_research.py --company "Example Corp" --verbose
```

Check the log file for detailed information:

```bash
tail -f company_research.log
```

## License

This tool is for internal use within Diligent Corporation for company research and due diligence purposes.

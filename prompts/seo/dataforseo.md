# DataForSEO Integration Prompt

## Context

Folosești DataForSEO API pentru:
- Keyword research și SERP analysis
- Backlink analysis
- On-page SEO audit
- Competitor analysis

## API Configuration

```python
# DataForSEO Credentials
DATAFORSEO_LOGIN = "your_login"
DATAFORSEO_PASSWORD = "your_password"
BASE_URL = "https://api.dataforseo.com"

# Germany Location Codes
LOCATIONS = {
    "germany": 2276,
    "hamburg": 1004234,
    "berlin": 1003854,
    "munich": 1004210,
    "frankfurt": 1004069
}

# Language
LANGUAGE_CODE = "de"
```

## Common API Endpoints

### 1. SERP Analysis

```python
# Endpoint: /v3/serp/google/organic/live/advanced

request = {
    "keyword": "Reinigungsservice Hamburg",
    "location_code": 2276,
    "language_code": "de",
    "device": "desktop",
    "os": "windows",
    "depth": 100
}

# Response parsing
for item in response["tasks"][0]["result"][0]["items"]:
    print(f"Position: {item['rank_absolute']}")
    print(f"URL: {item['url']}")
    print(f"Title: {item['title']}")
    print(f"Description: {item['description']}")
```

### 2. Keyword Search Volume

```python
# Endpoint: /v3/keywords_data/google/search_volume/live

request = {
    "keywords": [
        "Reinigungsservice Hamburg",
        "Büroreinigung Hamburg",
        "Gebäudereinigung Hamburg"
    ],
    "location_code": 2276,
    "language_code": "de"
}

# Response
{
    "keyword": "Reinigungsservice Hamburg",
    "search_volume": 1200,
    "competition": 0.65,
    "cpc": 2.50,
    "monthly_searches": [
        {"month": "2024-01", "search_volume": 1100},
        {"month": "2024-02", "search_volume": 1300}
    ]
}
```

### 3. Related Keywords

```python
# Endpoint: /v3/keywords_data/google/keywords_for_keywords/live

request = {
    "keyword": "Reinigungsservice",
    "location_code": 2276,
    "language_code": "de",
    "include_seed_keyword": true,
    "limit": 100
}
```

### 4. Keyword Suggestions

```python
# Endpoint: /v3/keywords_data/google/keyword_suggestions/live

request = {
    "keyword": "Gebäudereinigung",
    "location_code": 2276,
    "language_code": "de"
}
```

### 5. Backlinks Summary

```python
# Endpoint: /v3/backlinks/summary/live

request = {
    "target": "example.de",
    "include_subdomains": true
}

# Response
{
    "rank": 45,
    "backlinks": 1250,
    "referring_domains": 180,
    "referring_main_domains": 150,
    "dofollow": 1100,
    "nofollow": 150
}
```

### 6. On-Page SEO Audit

```python
# Step 1: Create Task
# Endpoint: /v3/on_page/task_post

request = {
    "target": "https://example.de/",
    "max_crawl_pages": 100,
    "enable_javascript": true,
    "enable_browser_rendering": true
}

# Step 2: Get Results
# Endpoint: /v3/on_page/pages

# Response includes:
# - Page speed metrics
# - Content analysis
# - Technical issues
# - Internal/external links
```

### 7. Competitor Domain Analysis

```python
# Endpoint: /v3/dataforseo_labs/google/competitors_domain/live

request = {
    "target": "example.de",
    "location_code": 2276,
    "language_code": "de",
    "limit": 20
}
```

## Python Helper Class

```python
import requests
import base64
from typing import Dict, List, Optional

class DataForSEO:
    def __init__(self, login: str, password: str):
        self.base_url = "https://api.dataforseo.com"
        credentials = f"{login}:{password}"
        self.headers = {
            "Authorization": f"Basic {base64.b64encode(credentials.encode()).decode()}",
            "Content-Type": "application/json"
        }

    def _request(self, endpoint: str, data: List[Dict]) -> Dict:
        response = requests.post(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            json=data
        )
        return response.json()

    def get_search_volume(self, keywords: List[str], location: int = 2276) -> Dict:
        """Get search volume for keywords in Germany"""
        return self._request(
            "/v3/keywords_data/google/search_volume/live",
            [{
                "keywords": keywords,
                "location_code": location,
                "language_code": "de"
            }]
        )

    def get_serp(self, keyword: str, location: int = 2276, depth: int = 10) -> Dict:
        """Get SERP results for keyword"""
        return self._request(
            "/v3/serp/google/organic/live/advanced",
            [{
                "keyword": keyword,
                "location_code": location,
                "language_code": "de",
                "depth": depth
            }]
        )

    def get_backlinks(self, domain: str) -> Dict:
        """Get backlink summary for domain"""
        return self._request(
            "/v3/backlinks/summary/live",
            [{
                "target": domain,
                "include_subdomains": True
            }]
        )

    def get_related_keywords(self, keyword: str, limit: int = 50) -> Dict:
        """Get related keywords"""
        return self._request(
            "/v3/keywords_data/google/keywords_for_keywords/live",
            [{
                "keyword": keyword,
                "location_code": 2276,
                "language_code": "de",
                "limit": limit
            }]
        )

# Usage
api = DataForSEO("login", "password")
results = api.get_search_volume(["Reinigungsservice Hamburg"])
```

## Output Templates

### Keyword Report
```markdown
# Keyword Analysis: [Keyword]

## Overview
- Search Volume: [X]/month
- Competition: [X]% ([Low/Medium/High])
- CPC: €[X]
- Trend: [↑/↓/→]

## SERP Analysis
| Position | Domain | URL |
|----------|--------|-----|
| 1 | [domain] | [url] |
| 2 | [domain] | [url] |

## Related Keywords
| Keyword | Volume | KD |
|---------|--------|-----|
| [kw] | [vol] | [kd]% |

## Recommendations
1. [recommendation]
2. [recommendation]
```

### Backlink Report
```markdown
# Backlink Analysis: [Domain]

## Summary
- Domain Rating: [X]
- Total Backlinks: [X]
- Referring Domains: [X]
- Dofollow Ratio: [X]%

## Top Referring Domains
| Domain | DR | Links |
|--------|-----|-------|
| [domain] | [dr] | [links] |

## Anchor Text Distribution
| Anchor | Count | % |
|--------|-------|---|
| [anchor] | [count] | [%] |
```

## Rate Limits & Best Practices

1. **Rate Limits**: Max 2000 requests/minute
2. **Batching**: Combine multiple keywords in one request
3. **Caching**: Cache results for 24h for static data
4. **Cost**: Monitor API credits usage
5. **Errors**: Implement retry logic with exponential backoff

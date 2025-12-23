# SEO Audit Prompt - WordPress Sites

## Rol și Context

Ești un expert SEO specializat în:
- WordPress SEO cu RankMath Pro
- SEO tehnic și on-page
- Local SEO pentru Germania
- Analiză competitivă cu DataForSEO

## Structura Audit SEO

### 1. Technical SEO

```markdown
## Technical SEO Checklist

### Indexare & Crawling
- [ ] Robots.txt configurat corect
- [ ] XML Sitemap generat și submis
- [ ] No index pe pagini irelevante
- [ ] Canonical tags implementate
- [ ] Hreflang pentru multi-language (de/en)

### Performance
- [ ] Core Web Vitals (LCP, FID, CLS)
- [ ] Page Speed Score > 80 mobile
- [ ] Imagini optimizate (WebP, lazy load)
- [ ] CSS/JS minificat
- [ ] Caching activat

### Mobile
- [ ] Mobile-friendly test OK
- [ ] Responsive design
- [ ] Touch elements spaced correctly
- [ ] Font size readable

### Security
- [ ] HTTPS activat
- [ ] SSL valid
- [ ] No mixed content
```

### 2. On-Page SEO

```markdown
## On-Page SEO Analysis

### Per Page Check
| Element | Status | Recomandare |
|---------|--------|-------------|
| Title Tag | ⚠️/✅/❌ | [recomandare] |
| Meta Description | | |
| H1 Tag | | |
| H2-H6 Structure | | |
| Image Alt Text | | |
| Internal Links | | |
| External Links | | |
| Keyword Density | | |
| Content Length | | |
| Schema Markup | | |

### RankMath Score
- Current Score: [X]/100
- Target Score: 80+/100
- Issues to fix: [list]
```

### 3. Content Analysis

```markdown
## Content Audit

### Quality Metrics
- Word count average: [X]
- Readability score: [X]
- Duplicate content: [%]
- Thin content pages: [list]

### Keyword Coverage
| Target Keyword | Current Rank | Search Volume | Difficulty |
|----------------|--------------|---------------|------------|
| [keyword] | [position] | [volume] | [KD%] |

### Content Gaps
- Missing topics: [list]
- Competitor content we don't have: [list]
```

### 4. Local SEO (pentru site-uri germane)

```markdown
## Local SEO Audit

### Google Business Profile
- [ ] Claimed & verified
- [ ] NAP consistent
- [ ] Categories correct
- [ ] Photos uploaded
- [ ] Reviews managed

### Local Citations
- [ ] Yelp Germany
- [ ] Gelbe Seiten
- [ ] Das Örtliche
- [ ] GoLocal
- [ ] 11880.com

### Local Keywords
| Keyword | City | Monthly Searches |
|---------|------|------------------|
| Reinigung [Stadt] | [City] | [Volume] |
```

### 5. Backlink Analysis

```markdown
## Backlink Profile

### Metrics
- Domain Rating (DR): [X]
- Referring Domains: [X]
- Backlinks Total: [X]
- Dofollow/Nofollow Ratio: [X]%

### Quality Assessment
- Toxic links: [count]
- High-quality links: [count]
- Anchor text distribution: [breakdown]

### Competitor Comparison
| Metric | Our Site | Competitor 1 | Competitor 2 |
|--------|----------|--------------|--------------|
| DR | | | |
| Backlinks | | | |
| Keywords | | | |
```

## Output Format

```markdown
# SEO Audit Report: [Site Name]
**Date:** [date]
**URL:** [url]
**Auditor:** Claude Code

## Executive Summary
[2-3 paragrafe rezumat]

## Priority Actions (Top 5)
1. 🔴 [Critical issue]
2. 🔴 [Critical issue]
3. 🟡 [Important issue]
4. 🟡 [Important issue]
5. 🟢 [Quick win]

## Detailed Findings
[sections above]

## Recommendations Timeline
| Priority | Action | Impact | Effort |
|----------|--------|--------|--------|
| High | [action] | High | Low |
| Medium | [action] | Medium | Medium |
| Low | [action] | Low | High |

## Next Steps
1. [immediate action]
2. [short-term action]
3. [long-term action]
```

## DataForSEO Integration

```python
# API Endpoints to use
endpoints = {
    "serp": "/v3/serp/google/organic/live/advanced",
    "keywords": "/v3/keywords_data/google/search_volume/live",
    "backlinks": "/v3/backlinks/summary/live",
    "onpage": "/v3/on_page/task_post"
}

# Example request
{
    "keyword": "Reinigungsservice Hamburg",
    "location_code": 2276,  # Germany
    "language_code": "de"
}
```

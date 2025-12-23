# Site Prompt: Reinigungsdienstleistungen

## Site Information

| Property | Value |
|----------|-------|
| **Domain** | reinigungsdienstleistungen.com |
| **Type** | WordPress |
| **Language** | DE |
| **Industry** | Cleaning Services |
| **Location** | Germany (National) |
| **VPS** | TBD |
| **Repository** | WP_ReinigungDistleistungen |

## Business Context

### Company Profile
- Portal național pentru servicii de curățenie
- Acoperire la nivel de Germania
- Posibil agregator sau serviciu direct

### Target Audience
- Clienți B2B și B2C din toată Germania
- Căutări generice (non-locale)
- Comparatori de prețuri

### Unique Selling Points
- Acoperire națională
- Varietate de servicii
- Platformă profesională

## SEO Strategy

### Primary Keywords (High Volume - National)
| Keyword | Volume | Priority |
|---------|--------|----------|
| Reinigungsdienstleistungen | ~1600 | High |
| Reinigungsfirma | ~5400 | High |
| Gebäudereinigung | ~6600 | High |
| Reinigungsservice | ~4400 | High |
| professionelle Reinigung | ~1300 | Medium |

### Content Strategy - National Focus
1. **Pillar Pages**: Comprehensive guides per service type
2. **City Pages**: Top 20 German cities
3. **Comparison Content**: Pricing guides, service comparisons
4. **Educational Content**: How-to guides, checklists

### Target Cities (Landing Pages)
Tier 1 (Population 500k+):
- Berlin, Hamburg, München, Köln, Frankfurt

Tier 2 (Population 200k-500k):
- Stuttgart, Düsseldorf, Leipzig, Dortmund, Essen

Tier 3 (Population 100k-200k):
- Hannover, Nürnberg, Dresden, Bremen, Bochum

## Page Structure

### Homepage
```
H1: Reinigungsdienstleistungen in Deutschland
- Hero: National service promise
- Service categories (visual grid)
- City coverage map
- How it works (3 steps)
- Trust signals (numbers, certifications)
- CTA: Get quote
```

### Service Pillar Pages
Long-form content (2000+ words):
- Gebäudereinigung - Complete Guide
- Büroreinigung - Everything You Need to Know
- Fensterreinigung - Professional Services
- Grundreinigung - Deep Cleaning Guide
- Industriereinigung - Commercial Solutions

### City Landing Pages
Template for each city:
```
H1: Reinigungsdienstleistungen in [City]
- Local intro
- Available services
- Why local service matters
- Pricing info
- Contact/Quote form
```

## Technical SEO

### Site Architecture
```
/                                    # Homepage
├── /dienstleistungen/              # Services hub
│   ├── /gebaudereinigung/          # Building cleaning
│   ├── /buroreinigung/             # Office cleaning
│   ├── /fensterreinigung/          # Window cleaning
│   └── /grundreinigung/            # Deep cleaning
├── /standorte/                     # Locations hub
│   ├── /berlin/                    # City page
│   ├── /hamburg/                   # City page
│   └── /munchen/                   # City page
├── /preise/                        # Pricing
├── /blog/                          # Blog
└── /kontakt/                       # Contact
```

### Schema Markup
```json
{
  "@type": "Organization",
  "name": "Reinigungsdienstleistungen",
  "url": "https://reinigungsdienstleistungen.com",
  "areaServed": {
    "@type": "Country",
    "name": "Germany"
  },
  "hasOfferCatalog": {
    "@type": "OfferCatalog",
    "name": "Reinigungsdienstleistungen",
    "itemListElement": [
      {"@type": "Service", "name": "Gebäudereinigung"},
      {"@type": "Service", "name": "Büroreinigung"},
      {"@type": "Service", "name": "Fensterreinigung"}
    ]
  }
}
```

## Content Templates

### Pillar Page Template (2000+ words)
```markdown
# [Service]: Der komplette Leitfaden für [Year]

## Was ist [Service]?
[Definition, 200 words]

## Arten von [Service]
[Types breakdown, 300 words]

## Vorteile professioneller [Service]
[Benefits, 250 words]

## [Service] Kosten: Was Sie erwarten können
[Pricing guide, 300 words]

## Wie wählt man die richtige [Service] Firma?
[Selection criteria, 300 words]

## [Service] Checkliste
[Checklist, 200 words]

## Häufig gestellte Fragen zu [Service]
[10 FAQs, 500 words]

## Fazit
[Summary + CTA, 150 words]
```

### City Page Template
```markdown
# Reinigungsdienstleistungen in [City]

Professionelle Reinigungsservices für [City] und Umgebung.

## Unsere Leistungen in [City]
- Gebäudereinigung
- Büroreinigung
- [Other services]

## Warum lokale Reinigungsfirmen in [City]?
[Local benefits]

## [City] Reinigung Preise
[Regional pricing info]

## Jetzt Angebot für [City] anfordern
[CTA + Form]
```

## Keyword Mapping

### Homepage
- Primary: Reinigungsdienstleistungen
- Secondary: professionelle Reinigung Deutschland, Reinigungsfirma finden

### Service Pages
| Page | Primary Keyword | Secondary |
|------|-----------------|-----------|
| /gebaudereinigung/ | Gebäudereinigung | Gebäudereinigung Firma, professionelle Gebäudereinigung |
| /buroreinigung/ | Büroreinigung | Büroreinigung Kosten, Büroreinigung Firma |
| /fensterreinigung/ | Fensterreinigung | Fensterreinigung Preise, professionelle Fensterreinigung |

### City Pages
| City | Primary Keyword |
|------|-----------------|
| /berlin/ | Reinigungsdienstleistungen Berlin |
| /hamburg/ | Reinigungsdienstleistungen Hamburg |
| /munchen/ | Reinigungsdienstleistungen München |

## Quality Standards

### Content Requirements
- Minimum 1500 words for pillar pages
- Minimum 800 words for city pages
- Original content (no duplicates)
- Updated annually

### SEO Requirements
- RankMath score 85+ for all pages
- Schema markup implemented
- Internal linking strategy
- Image optimization

## Workflow

```bash
# Access project
cd /home/george/WP-ADMIN/WP_ReinigungDistleistungen

# Content creation workflow
1. Research keywords (DataForSEO)
2. Create content outline
3. Write content in German
4. Optimize with RankMath
5. Add schema markup
6. Publish and index
```

## Monthly Tasks
- [ ] Publish 2-4 new city pages
- [ ] Update 1 pillar page
- [ ] Create 2 blog posts
- [ ] Monitor rankings
- [ ] Competitor analysis
- [ ] Technical SEO audit

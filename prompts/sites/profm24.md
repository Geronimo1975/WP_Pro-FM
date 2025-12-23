# Site Prompt: Pro-FM 24

## Site Information

| Property | Value |
|----------|-------|
| **Domain** | profm24.de |
| **Type** | WordPress + Django Backend |
| **Language** | DE |
| **Industry** | Facility Management |
| **Location** | Germany |
| **VPS** | 217.154.250.85 |
| **Repository** | WP_Pro-FM |

## Business Context

### Company Profile
- Facility Management profesional
- Servicii B2B pentru companii și administrații
- Focus pe contracte pe termen lung
- Servicii integrate de management al clădirilor

### Target Audience
- Corporate clients (B2B)
- Property managers
- Administrații de clădiri
- Companii cu spații mari

### Services Offered
- Facility Management complet
- Gebäudemanagement
- Technisches Facility Management
- Infrastrukturelles Facility Management
- Kaufmännisches Facility Management

## SEO Strategy

### Primary Keywords (B2B Focus)
| Keyword | Volume | Priority |
|---------|--------|----------|
| Facility Management | ~6600 | High |
| Facility Management Firma | ~720 | High |
| Gebäudemanagement | ~1900 | High |
| FM Dienstleister | ~390 | Medium |
| Technisches Facility Management | ~480 | Medium |

### B2B Content Strategy
1. **Thought Leadership**: Industry insights, whitepapers
2. **Case Studies**: Success stories with metrics
3. **Service Deep Dives**: Detailed service explanations
4. **Industry Guides**: FM best practices

### Target Industries
- Bürogebäude (Office Buildings)
- Einkaufszentren (Shopping Centers)
- Industrieanlagen (Industrial Facilities)
- Krankenhäuser (Hospitals)
- Bildungseinrichtungen (Educational Institutions)

## Technical Architecture

### Django Backend
```
Location: /var/www/profm24/
Stack: Django + PostgreSQL + Redis + Celery
Apps: content, media, seo, email_marketing, front_page, glossary
API: /api/ prefix
Admin: /admin/ (Unfold theme)
```

### Docker Services
```yaml
services:
  - db (PostgreSQL 16)
  - redis (Redis 7)
  - backend (Django)
  - celery (Worker)
  - celery-beat (Scheduler)
  - nginx (Production)
```

## Page Structure

### Homepage
```
H1: Professionelles Facility Management für Ihr Unternehmen
- Hero: B2B value proposition
- Services overview (FM Leistungen)
- Industries served
- Key metrics (buildings managed, years experience)
- Client logos
- CTA: Beratungsgespräch vereinbaren
```

### Service Pages
- Technisches Facility Management
- Infrastrukturelles Facility Management
- Kaufmännisches Facility Management
- Gebäudemanagement
- Property Management

### Industry Pages
- FM für Bürogebäude
- FM für Einzelhandel
- FM für Industrie
- FM für Gesundheitswesen
- FM für Bildung

### Resources
- Blog / Aktuelles
- Whitepaper Downloads
- Case Studies
- Glossar (FM Terms)

## Content Guidelines

### Brand Voice
- Professionell și expert
- B2B tone (formal)
- Data-driven și soluție-orientat
- Încredere și competență

### Writing Style
- Sie-Form (formal address)
- Technical accuracy
- Industry terminology
- Clear value propositions

### Terminology
| English | German |
|---------|--------|
| Facility Management | Facility Management (accepted) |
| Building Management | Gebäudemanagement |
| Property Management | Immobilienmanagement |
| Maintenance | Instandhaltung |
| Operations | Betrieb |
| Service Level Agreement | Service Level Agreement (SLA) |

## Schema Markup

```json
{
  "@type": "ProfessionalService",
  "name": "Pro-FM 24",
  "description": "Professionelles Facility Management",
  "url": "https://profm24.de",
  "serviceType": [
    "Facility Management",
    "Gebäudemanagement",
    "Property Management"
  ],
  "areaServed": {
    "@type": "Country",
    "name": "Germany"
  },
  "hasOfferCatalog": {
    "@type": "OfferCatalog",
    "name": "FM Dienstleistungen"
  }
}
```

## Workflow Commands

```bash
# Access project
cd /home/george/WP-ADMIN/WP_Pro-FM

# Docker management
make start              # Full start
make up                 # Start containers
make down               # Stop containers
make logs-backend       # View logs

# Django commands
make migrate            # Run migrations
make shell              # Django shell
make test               # Run tests

# Deploy to VPS
./deploy.sh
# or manual:
ssh profm@217.154.250.85 "cd /var/www/profm24 && git pull && docker-compose up -d"
```

## AI Content Generation

### Celery Tasks
- Content generation cu OpenAI
- SEO optimization
- Email campaigns
- Media sync

### Content Pipeline
```
1. Topic Research (DataForSEO)
2. Outline Generation (Claude/GPT)
3. Content Writing (AI + Human Edit)
4. SEO Optimization (RankMath)
5. Review & Publish
```

## Quality Standards

### B2B Content Requirements
- Minimum 1500 words for service pages
- Data and statistics included
- Professional imagery
- Clear CTAs (consultation, quote)
- Trust signals (certifications, clients)

### SEO Requirements
- RankMath score 85+
- Schema markup (ProfessionalService)
- Internal linking to services
- Industry-relevant backlinks target

## Monthly Tasks
- [ ] Publish 1-2 blog articles
- [ ] Update service pages if needed
- [ ] Create/update case study
- [ ] Email newsletter
- [ ] LinkedIn content sync
- [ ] Monitor B2B keywords
- [ ] Competitor analysis

## Integration Points

### WordPress REST API
```
Base: https://profm24.de/wp-json/wp/v2/
Auth: Application Password
```

### Django Admin API
```
Base: https://admin.profm24.de/api/
Auth: Token-based
Docs: /api/docs/
```

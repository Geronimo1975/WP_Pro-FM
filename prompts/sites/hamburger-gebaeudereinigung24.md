# Site Prompt: Hamburger Gebäudereinigung 24

## Site Information

| Property | Value |
|----------|-------|
| **Domain** | hamburger-gebaeudereinigung24.de |
| **Type** | WordPress |
| **Language** | DE |
| **Industry** | Cleaning Services |
| **Location** | Hamburg, Germany |
| **VPS** | TBD |
| **Repository** | WP_Hamburger-geneudereinigung24 |

## Business Context

### Company Profile
- Servicii de curățenie pentru Hamburg și zona metropolitană
- Focus pe disponibilitate 24/7
- Răspuns rapid pentru urgențe

### Target Audience
- Companii din Hamburg (birouri, restaurante, hoteluri)
- Proprietari rezidențiali
- Property managers

### Unique Selling Points
- Disponibilitate 24 ore
- Acoperire întreaga zonă Hamburg
- Servicii de urgență

## SEO Strategy

### Primary Keywords
| Keyword | Volume | Priority |
|---------|--------|----------|
| Gebäudereinigung Hamburg | ~2400 | High |
| Reinigungsservice Hamburg | ~1900 | High |
| Büroreinigung Hamburg | ~1000 | High |
| Reinigungsfirma Hamburg | ~880 | Medium |
| 24 Stunden Reinigung Hamburg | ~200 | Medium |

### Local SEO - Hamburg Districts
Target pages pentru fiecare district:
- Reinigung Hamburg Altona
- Reinigung Hamburg Eimsbüttel
- Reinigung Hamburg Wandsbek
- Reinigung Hamburg Harburg
- Reinigung Hamburg Bergedorf
- Reinigung Hamburg Nord
- Reinigung Hamburg Mitte

### Content Strategy
1. District-specific landing pages
2. Service pages detailiate
3. Blog: Cleaning tips, industry news
4. FAQ section

## Translation Requirements

### If translating from EN
Urmează regulile din `translation/base.md` cu focus pe:
- Hamburg-specific terminology
- Local landmarks și referințe
- 24/7 availability messaging

### Brand Voice
- Profesional și eficient
- Emphasis pe rapiditate
- Încredere și fiabilitate
- "Immer für Sie da" (Always there for you)

## Page Structure

### Homepage
```
H1: Professionelle Gebäudereinigung in Hamburg - 24/7 Service
- Hero mit CTA
- Services Grid (6 main services)
- Stadtteile Coverage Map
- Warum wir? (USPs)
- Kundenstimmen
- Kontaktformular
```

### Service Pages
- Büroreinigung Hamburg
- Fensterreinigung Hamburg
- Grundreinigung Hamburg
- Teppichreinigung Hamburg
- Treppenhausreinigung Hamburg
- Gastronomiereinigung Hamburg

### Area Pages (per District)
Template:
```
H1: [Service] in Hamburg [District]
- Local intro (2-3 sentences about district)
- Services available
- Why local matters
- CTA
```

## Technical SEO

### Schema Markup
```json
{
  "@type": "LocalBusiness",
  "name": "Hamburger Gebäudereinigung 24",
  "address": {
    "addressLocality": "Hamburg",
    "addressRegion": "HH",
    "addressCountry": "DE"
  },
  "areaServed": [
    {"@type": "City", "name": "Hamburg"},
    {"@type": "Place", "name": "Hamburg Altona"},
    {"@type": "Place", "name": "Hamburg Eimsbüttel"}
  ],
  "openingHoursSpecification": {
    "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "opens": "00:00",
    "closes": "23:59"
  }
}
```

### RankMath Settings
- Focus keyword per page
- Schema type: LocalBusiness
- Breadcrumbs enabled
- XML Sitemap: enabled

## Content Templates

### Service Page Template
```markdown
# [Service] in Hamburg

[2-3 sentences intro with main keyword]

## Unsere [Service] Leistungen

[Bullet points of what's included]

## Warum [Company] für Ihre [Service]?

[3-4 USPs]

## [Service] Preise

[Pricing info or "Kostenloses Angebot" CTA]

## Häufig gestellte Fragen

[3-5 FAQs with Schema]

## Jetzt [Service] anfragen

[Contact form]
```

### District Page Template
```markdown
# [Service] in Hamburg [District]

Als Ihr lokaler Partner für [Service] in [District] sind wir schnell vor Ort.

## Unsere Leistungen in [District]
[Services list]

## Schnelle Anfahrt nach [District]
[Local info]

## Jetzt Termin vereinbaren
[CTA]
```

## Workflow

```bash
# Access project
cd /home/george/WP-ADMIN/WP_Hamburger-geneudereinigung24

# Deploy changes
rsync -avz --progress \
    --exclude='.git' \
    ./ user@vps:/var/www/hamburger-gebaeudereinigung24/
```

## Quality Checklist

- [ ] All pages in German (Hochdeutsch)
- [ ] RankMath score 80+ per page
- [ ] District pages created
- [ ] Google Business Profile optimized
- [ ] NAP consistent everywhere
- [ ] Schema markup on all pages
- [ ] Mobile responsive
- [ ] Page speed > 80

## Monthly Tasks
- [ ] New blog post (Hamburg cleaning tips)
- [ ] Check rankings for main keywords
- [ ] Review competitor changes
- [ ] Update seasonal content
- [ ] Google Business posts

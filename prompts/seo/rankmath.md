# RankMath Pro Optimization Prompt

## Context

Optimizezi conținut WordPress folosind RankMath Pro pentru a obține scor 80+/100.

## RankMath Score Factors

### Basic SEO (40 points)

| Factor | Points | Requirement |
|--------|--------|-------------|
| Focus Keyword in Title | 5 | Keyword la începutul title |
| Focus Keyword in Meta | 5 | Keyword în meta description |
| Focus Keyword in URL | 5 | Keyword în slug |
| Focus Keyword in Content | 5 | Keyword în primele 100 cuvinte |
| Content Length | 10 | Min 600 cuvinte (ideal 1500+) |
| Focus Keyword Density | 5 | 1-1.5% din content |
| Focus Keyword in Subheading | 5 | Keyword în cel puțin un H2/H3 |

### Additional SEO (30 points)

| Factor | Points | Requirement |
|--------|--------|-------------|
| Internal Links | 5 | Min 1 internal link |
| External Links | 5 | Min 1 external link (dofollow) |
| Image Alt Attributes | 5 | Keyword în alt text imagine |
| Keyword in Image Title | 5 | Keyword în titlu imagine |
| Table of Contents | 5 | TOC pentru articole lungi |
| Schema Markup | 5 | Schema implementat |

### Title & Meta (15 points)

| Factor | Points | Requirement |
|--------|--------|-------------|
| Title Length | 5 | 50-60 caractere |
| Meta Description Length | 5 | 120-155 caractere |
| Power Words in Title | 5 | Cuvinte care atrag click |

### Readability (15 points)

| Factor | Points | Requirement |
|--------|--------|-------------|
| Paragraph Length | 5 | Max 120 cuvinte/paragraf |
| Sentence Length | 5 | Max 20 cuvinte/propoziție medie |
| Use of Subheadings | 5 | H2/H3 la fiecare 300 cuvinte |

## Optimization Checklist

```markdown
## RankMath Optimization: [Page Title]

### Focus Keyword
- Primary: [keyword]
- Secondary: [keyword 2], [keyword 3]

### Title Tag
- [ ] Keyword at beginning
- [ ] Length: [X]/60 chars
- [ ] Power word included
- [ ] Brand at end (optional)

**Current:** [title]
**Optimized:** [new title]

### Meta Description
- [ ] Keyword included
- [ ] Length: [X]/155 chars
- [ ] CTA included
- [ ] Compelling copy

**Current:** [meta]
**Optimized:** [new meta]

### URL/Slug
- [ ] Keyword in URL
- [ ] Short and clean
- [ ] No stop words

**Current:** /[slug]
**Optimized:** /[new-slug]

### Content Optimization
- [ ] Keyword in first 100 words
- [ ] Keyword density: [X]%
- [ ] Keyword in H2 subheading
- [ ] Word count: [X] (min 600)

### Media
- [ ] Featured image set
- [ ] Image alt with keyword
- [ ] Image title with keyword
- [ ] Images compressed

### Links
- [ ] Internal links: [X] (min 1)
- [ ] External links: [X] (min 1)
- [ ] Broken links: [check]

### Schema Markup
- [ ] Schema type: [Article/LocalBusiness/Service]
- [ ] All required fields filled

### Readability
- [ ] Short paragraphs (≤120 words)
- [ ] Short sentences (avg ≤20 words)
- [ ] Subheadings every 300 words
- [ ] Bullet points used
- [ ] Transition words used

## Score Tracking
| Before | After | Target |
|--------|-------|--------|
| [X]/100 | [X]/100 | 80+/100 |
```

## Power Words (German)

### Urgency
- Jetzt, Sofort, Heute, Limitiert, Exklusiv

### Trust
- Professionell, Zertifiziert, Garantiert, Bewährt, Geprüft

### Value
- Kostenlos, Gratis, Sparen, Günstig, Rabatt

### Emotion
- Erstaunlich, Perfekt, Einfach, Schnell, Sicher

## Schema Markup Templates

### LocalBusiness (Cleaning Company)
```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "[Company Name]",
  "description": "[Description]",
  "url": "[URL]",
  "telephone": "[Phone]",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "[Street]",
    "addressLocality": "[City]",
    "postalCode": "[PLZ]",
    "addressCountry": "DE"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "[lat]",
    "longitude": "[lng]"
  },
  "openingHours": "Mo-Fr 08:00-18:00",
  "priceRange": "€€"
}
```

### Service
```json
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "[Service Name]",
  "description": "[Description]",
  "provider": {
    "@type": "LocalBusiness",
    "name": "[Company]"
  },
  "areaServed": {
    "@type": "City",
    "name": "[City]"
  }
}
```

### FAQ
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "[Question]",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[Answer]"
      }
    }
  ]
}
```

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Keyword not in title | Move keyword to beginning |
| Title too long | Shorten to 60 chars |
| Meta too short | Add CTA and benefits |
| Low content length | Add FAQ section, more details |
| No internal links | Link to related services/posts |
| Missing alt text | Add descriptive alt with keyword |
| Poor readability | Break up paragraphs, add bullets |

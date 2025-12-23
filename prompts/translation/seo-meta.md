# Translation Prompt - SEO Meta Tags (EN→DE)

## Context
Traduci și optimizezi meta tags pentru SEO în limba germană, compatibil cu RankMath Pro.

## Specificații RankMath

### Title Tag
- **Lungime maximă:** 60 caractere
- **Format recomandat:** `Primary Keyword | Brand` sau `Primary Keyword - Secondary | Brand`
- **Variabile RankMath:** `%title%`, `%sitename%`, `%sep%`

### Meta Description
- **Lungime optimă:** 150-155 caractere
- **Structură:** Beneficiu + Keyword + CTA
- **Include:** emoji (opțional), numere, call-to-action

### Focus Keyword
- Keyword principal în germană
- Variante long-tail
- Keywords locale (oraș, regiune)

## Reguli de Traducere SEO

### 1. Keywords Mapping
```
cleaning services → Reinigungsdienstleistungen
cleaning company → Reinigungsfirma, Reinigungsunternehmen
professional cleaning → professionelle Reinigung
house cleaning → Hausreinigung
office cleaning → Büroreinigung
```

### 2. Modificatori Locali
```
[City] cleaning → Reinigung [Stadt]
cleaning services in [City] → Reinigungsdienstleistungen in [Stadt]
best cleaning [City] → beste Reinigung [Stadt]
```

### 3. Intent Keywords
```
# Informational
how to clean → wie reinigen
cleaning tips → Reinigungstipps

# Commercial
cleaning prices → Reinigung Preise
cleaning quote → Reinigung Angebot

# Transactional
book cleaning → Reinigung buchen
hire cleaner → Reinigungskraft beauftragen
```

## Output Format

```yaml
# SEO Meta Translation

page_slug: "[slug-original]"
page_slug_de: "[slug-german]"

title:
  original: "[EN title]"
  translated: "[DE title]"
  characters: [count]

meta_description:
  original: "[EN description]"
  translated: "[DE description]"
  characters: [count]

focus_keyword:
  primary: "[main keyword DE]"
  secondary:
    - "[keyword 2]"
    - "[keyword 3]"

rankmath_score_tips:
  - "[suggestion 1]"
  - "[suggestion 2]"
```

## Exemple per Industrie

### Cleaning Services
```yaml
title:
  original: "Professional Cleaning Services | CleanCo"
  translated: "Professionelle Reinigungsdienstleistungen | CleanCo"
  characters: 52

meta_description:
  original: "Top-rated cleaning services for homes and offices. Get a free quote today!"
  translated: "Erstklassige Reinigungsdienstleistungen für Privat und Gewerbe. Jetzt kostenloses Angebot anfordern!"
  characters: 103

focus_keyword:
  primary: "Reinigungsdienstleistungen"
  secondary:
    - "professionelle Reinigung"
    - "Gebäudereinigung"
```

### Local Business (Hamburg)
```yaml
title:
  original: "Cleaning Services Hamburg | Best Cleaners"
  translated: "Reinigungsservice Hamburg | Ihre Reinigungsprofis"
  characters: 51

meta_description:
  original: "Looking for reliable cleaning in Hamburg? We offer professional cleaning services. Call now!"
  translated: "Suchen Sie zuverlässige Reinigung in Hamburg? Professioneller Reinigungsservice. Jetzt anrufen!"
  characters: 98

focus_keyword:
  primary: "Reinigungsservice Hamburg"
  secondary:
    - "Reinigung Hamburg"
    - "Gebäudereinigung Hamburg"
```

## Checklist SEO Meta

- [ ] Title ≤ 60 caractere
- [ ] Meta description 150-155 caractere
- [ ] Focus keyword în title
- [ ] Focus keyword în meta description
- [ ] CTA în meta description
- [ ] Nu există duplicate
- [ ] Slug URL-friendly (lowercase, hyphens)

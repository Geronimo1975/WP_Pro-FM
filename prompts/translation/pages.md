# Translation Prompt - WordPress Pages (EN→DE)

## Context
Traduci pagini WordPress din engleză în germană pentru site-uri de servicii de curățenie.

## Instrucțiuni Specifice Pagini

### 1. Structura Paginii
Păstrează exact structura originală:
- Headings (H1, H2, H3) - traduse
- Paragrafe - traduse
- Liste - traduse
- Butoane/CTA - traduse și adaptate
- Imagini - păstrează, traduce doar alt text

### 2. Elemente WordPress
```
[elementor] → păstrează shortcode-urile
{{placeholder}} → păstrează placeholder-urile
[contact-form-7 id="123"] → păstrează
```

### 3. Call-to-Action (CTA)
| Original | Traducere |
|----------|-----------|
| Get a Quote | Angebot anfordern |
| Contact Us | Kontaktieren Sie uns |
| Learn More | Mehr erfahren |
| Book Now | Jetzt buchen |
| Free Estimate | Kostenlose Schätzung |
| Call Now | Jetzt anrufen |

### 4. Pagini Comune

#### Homepage
- Hero section: impact maxim, CTA clar
- Services overview: beneficii, nu features
- Trust signals: certificări, ani experiență

#### About Us (Über uns)
- Istorie companiei
- Valori și misiune
- Echipa (dacă e cazul)

#### Services (Dienstleistungen)
- Descrieri detaliate servicii
- Beneficii pentru client
- Prețuri (dacă sunt menționate)

#### Contact (Kontakt)
- Formular contact
- Informații companie
- Program de lucru

## Workflow

1. **Analizează** pagina originală
2. **Identifică** elementele cheie (headings, CTA, keywords)
3. **Traduce** secțiune cu secțiune
4. **Verifică** consistența terminologiei
5. **Optimizează** pentru SEO german

## Output Format

```markdown
# Traducere Pagină: [Nume Pagină]

## Meta Information
- **Title (DE):** [max 60 chars]
- **Meta Description (DE):** [max 155 chars]
- **Slug (DE):** [url-friendly]

## Content

### [Section Name]
**Original:**
[text EN]

**Traducere:**
[text DE]

---

## Checklist
- [ ] Toate headings traduse
- [ ] CTA-uri adaptate
- [ ] Keywords SEO incluse
- [ ] Formatare păstrată
- [ ] Lungime meta tags OK
```

## Exemplu Complet

### Input (About Page)
```html
<h1>About Our Cleaning Company</h1>
<p>With over 10 years of experience, we provide top-quality cleaning services.</p>
<a href="/contact" class="btn">Get Your Free Quote</a>
```

### Output
```html
<h1>Über unser Reinigungsunternehmen</h1>
<p>Mit über 10 Jahren Erfahrung bieten wir erstklassige Reinigungsdienstleistungen.</p>
<a href="/kontakt" class="btn">Kostenloses Angebot anfordern</a>
```

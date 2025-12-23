# Site Prompt: Gebäudereinigung Buchholz

## Site Information

| Property | Value |
|----------|-------|
| **Domain** | gebäudereinigung-buchholz.de |
| **Type** | WordPress + WPML |
| **Languages** | DE (primary), EN (source) |
| **Industry** | Cleaning Services |
| **Location** | Buchholz in der Nordheide, Germany |
| **VPS** | 217.154.250.85 |
| **Repository** | WP_Gebaudereinigung-Buchholz |

## Business Context

### Company Profile
- Servicii de curățenie pentru zona Buchholz și împrejurimi
- Focus pe curățenie comercială și rezidențială
- Piață locală, radius ~50km

### Target Audience
- Companii locale (birouri, magazine)
- Proprietari de case și apartamente
- Administrații de clădiri

### Competitors
1. [competitor1.de]
2. [competitor2.de]
3. [competitor3.de]

## SEO Strategy

### Primary Keywords
| Keyword | Volume | Priority |
|---------|--------|----------|
| Gebäudereinigung Buchholz | [vol] | High |
| Reinigungsservice Buchholz | [vol] | High |
| Büroreinigung Buchholz | [vol] | Medium |
| Fensterreinigung Buchholz | [vol] | Medium |

### Local SEO Focus
- Google Business Profile optimization
- Local citations (Gelbe Seiten, Das Örtliche)
- Reviews management
- NAP consistency

### Content Strategy
1. Service pages per tip de curățenie
2. Area pages pentru localități din zonă
3. Blog posts cu tips și guides

## Translation Rules

### Specific Terminology
| English | German |
|---------|--------|
| Buchholz cleaning | Reinigung Buchholz |
| our team | unser Team |
| years of experience | Jahre Erfahrung |
| free quote | kostenloses Angebot |

### Brand Voice
- Professional dar prietenos
- Local și de încredere
- Emphasis pe calitate și puntualitate

### Do NOT translate
- Buchholz (nume loc)
- Brand name
- Phone numbers
- Email addresses

## Workflow Commands

```bash
# Access project
cd /home/george/WP-ADMIN/WP_Gebaudereinigung-Buchholz

# Activate environment
source venv/bin/activate
cd WPML

# Check translation status
python main.py status

# Translate specific page
python main.py translate --type page --id [ID] --apply

# Batch translate
python main.py translate-all --type pages --limit 5 --apply

# SEO analysis
cd ../SEO
python manager.py analyze
```

## Page Structure

### Homepage
- Hero: Main service + CTA
- Services overview (4-6 main services)
- Why choose us (trust signals)
- Testimonials
- Contact form

### Service Pages
- Büroreinigung
- Fensterreinigung
- Grundreinigung
- Teppichreinigung
- Unterhaltsreinigung

### Area Pages
- Reinigung Buchholz
- Reinigung Harburg
- Reinigung Tostedt
- Reinigung Seevetal

## Quality Checklist

### Before Publishing
- [ ] Content tradus în Hochdeutsch
- [ ] RankMath score 80+
- [ ] Images optimized
- [ ] Internal links added
- [ ] Schema markup (LocalBusiness)
- [ ] Meta tags complete
- [ ] Mobile preview checked

### Monthly Tasks
- [ ] Check Google Search Console
- [ ] Update content if needed
- [ ] Add new blog post
- [ ] Review and respond to reviews
- [ ] Check page speed

## API Integration

### WordPress REST API
```
Base URL: https://xn--gebudereinigung-buchholz-sbc.de/wp-json/wp/v2/
Auth: Basic Auth (app password)
```

### WPML Endpoints
```
Languages: /wpml/v1/languages
Translations: ?wpml_language=de|en
```

## Contact

- **Phone:** [phone]
- **Email:** [email]
- **Address:** [address], Buchholz

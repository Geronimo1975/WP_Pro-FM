# On-Page SEO Checklist für PROFM24

## Heading-Struktur (H1-H3)

### Homepage
```
H1: Facility Management Hamburg – PROFM24
  H2: Unsere Dienstleistungen
    H3: Technisches Gebäudemanagement
    H3: Gebäudereinigung
    H3: Hausmeisterservice
    H3: Energiemanagement
  H2: Warum PROFM24?
    H3: Lokal in Hamburg
    H3: Erfahrenes Team
    H3: Faire Preise
  H2: Unsere Servicegebiete in Hamburg
  H2: Kontakt & Beratung
```

### Wichtige Regeln:
- [ ] **Nur 1x H1 pro Seite** (enthält Haupt-Keyword)
- [ ] H2 für Hauptabschnitte
- [ ] H3 für Unterabschnitte
- [ ] Keywords natürlich in Headings integrieren

---

## Interne Verlinkung

### Empfohlene Link-Struktur:
```
Homepage
├── /dienstleistungen/
│   ├── /gebaeudemanagement/
│   ├── /gebaeudereinigung/
│   ├── /hausmeisterservice/
│   └── /energiemanagement/
├── /ueber-uns/
├── /servicegebiete/
│   ├── /hamburg-eimsbuettel/
│   ├── /hamburg-altona/
│   └── /hamburg-wandsbek/
├── /referenzen/
├── /blog/
└── /kontakt/
```

### Interne Links Best Practices:
- [ ] Von jeder Dienstleistungsseite zur Homepage verlinken
- [ ] Zwischen verwandten Services verlinken
- [ ] Blog-Artikel zu passenden Service-Seiten verlinken
- [ ] "Breadcrumb Navigation" aktivieren
- [ ] Footer mit wichtigsten Seiten

### Anchor-Text Beispiele:
- "Facility Management in Hamburg" → Homepage
- "professionelle Gebäudereinigung" → /gebaeudereinigung/
- "Hausmeisterservice anfragen" → /kontakt/
- "unsere Referenzen ansehen" → /referenzen/

---

## Mobile-Friendliness

### Technische Anforderungen:
- [ ] Responsive Design (alle Breakpoints testen)
- [ ] Touch-Targets mindestens 48x48px
- [ ] Lesbare Schriftgröße (min. 16px)
- [ ] Kein horizontales Scrollen
- [ ] Viewport Meta-Tag korrekt gesetzt

### Test-Tools:
- Google Mobile-Friendly Test: https://search.google.com/test/mobile-friendly
- Chrome DevTools (Device Mode)
- BrowserStack für echte Gerätetests

---

## Ladegeschwindigkeit

### Core Web Vitals Ziele:
- [ ] **LCP** (Largest Contentful Paint): < 2.5s
- [ ] **FID** (First Input Delay): < 100ms
- [ ] **CLS** (Cumulative Layout Shift): < 0.1

### Optimierungsmaßnahmen:
- [ ] Bilder komprimieren (WebP Format)
- [ ] Lazy Loading für Bilder aktivieren
- [ ] CSS/JS minimieren und kombinieren
- [ ] Browser-Caching aktivieren
- [ ] CDN verwenden
- [ ] Kritisches CSS inline
- [ ] Unnötige Plugins deaktivieren

### Test-Tools:
- PageSpeed Insights: https://pagespeed.web.dev/
- GTmetrix: https://gtmetrix.com/
- WebPageTest: https://www.webpagetest.org/

---

## Google Maps Integration

### Embed Code (Responsive):
```html
<div class="google-maps-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
  <iframe
    src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d151928.74609775517!2d9.84170815!3d53.55034295!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x47b161837e1813b9%3A0x4263df27bd63aa0!2sHamburg!5e0!3m2!1sde!2sde!4v1704628800000!5m2!1sde!2sde"
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;"
    allowfullscreen=""
    loading="lazy"
    referrerpolicy="no-referrer-when-downgrade"
    title="PROFM24 Standort Hamburg">
  </iframe>
</div>
```

### Best Practices:
- [ ] `loading="lazy"` für Performance
- [ ] `title` Attribut für Accessibility
- [ ] Responsive Container (56.25% = 16:9)
- [ ] Google Maps API Key für erweiterte Features
- [ ] Schema.org GeoCoordinates parallel nutzen

### Kontaktseite Layout:
```
+---------------------------+
|     Kontaktformular       |
+---------------------------+
|     Google Maps           |
+---------------------------+
| Adresse | Tel | E-Mail    |
+---------------------------+
| Öffnungszeiten            |
+---------------------------+
```

---

## Zusätzliche Local SEO Maßnahmen

### Google Business Profile:
- [ ] Profil vollständig ausfüllen
- [ ] Korrekte Kategorie: "Facility Management Service"
- [ ] Fotos regelmäßig hochladen
- [ ] Auf Bewertungen antworten
- [ ] Posts regelmäßig veröffentlichen
- [ ] Q&A Bereich aktiv nutzen

### NAP Konsistenz (Name, Address, Phone):
- [ ] Überall identische Schreibweise
- [ ] Wichtige Verzeichnisse:
  - Google Business Profile
  - Bing Places
  - Apple Maps
  - Yelp
  - Das Örtliche
  - Gelbe Seiten
  - Branchenbuch Deutschland

### Lokale Keywords:
```
Primär:
- Facility Management Hamburg
- Gebäudemanagement Hamburg
- Hausmeisterservice Hamburg

Sekundär (Stadtteile):
- Facility Management Eimsbüttel
- Gebäudereinigung Altona
- Hausmeister Wandsbek
- Gebäudeservice Schnelsen

Long-Tail:
- Facility Management Unternehmen Hamburg
- professionelle Gebäudeverwaltung Hamburg
- technisches Gebäudemanagement Hamburger Unternehmen
```

---

## Quick Wins Checkliste

### Sofort umsetzbar:
- [ ] Meta Title & Description optimieren
- [ ] H1 mit Haupt-Keyword
- [ ] JSON-LD Schema einbinden
- [ ] Google Maps auf Kontaktseite
- [ ] Telefonnummer klickbar machen
- [ ] Alt-Texte für alle Bilder
- [ ] SSL-Zertifikat aktiv

### Diese Woche:
- [ ] Google Business Profile optimieren
- [ ] NAP in Footer einheitlich
- [ ] Interne Verlinkung verbessern
- [ ] Core Web Vitals prüfen

### Diesen Monat:
- [ ] Lokale Landingpages erstellen
- [ ] Bewertungen sammeln
- [ ] Blog mit lokalem Content starten
- [ ] Backlinks von lokalen Seiten

# ProFM24 Facility Management Glossar

AI-gestütztes Glossar-System für profm24.de mit 535+ Fachbegriffen zu Smart Building, IoT, Robotik und nachhaltigem Facility Management.

## Quick Start

```bash
# 1. Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. Datenbank starten (Docker)
docker run -d \
  --name profm-glossar-db \
  -e POSTGRES_DB=profm_glossar \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5433:5432 \
  postgres:16

# 4. Schema initialisieren
psql -h localhost -p 5433 -U postgres -d profm_glossar -f init.sql

# 5. Konfiguration prüfen
cp .env.example .env
# .env mit eigenen Werten anpassen

# 6. Test-Term generieren
python generate_terms.py --test
```

## Scripts

### generate_terms.py - Term-Generierung

```bash
# Statistiken anzeigen
python generate_terms.py --stats

# Test: 1 Term generieren
python generate_terms.py --test

# Terme für Buchstabe generieren
python generate_terms.py --letter A --count 10

# Terme für Kategorie generieren
python generate_terms.py --category "Smart Building & IoT" --count 20

# Alle fehlenden Terme generieren
python generate_terms.py --all

# Priorität-1 Terme generieren
python generate_terms.py --priority 1
```

### sync_to_wordpress.py - WordPress Sync

```bash
# Verbindung testen
python sync_to_wordpress.py --test

# Status anzeigen
python sync_to_wordpress.py --status

# Hub-Seite erstellen
python sync_to_wordpress.py --create-hub

# Buchstaben-Seiten erstellen
python sync_to_wordpress.py --create-letters

# Kategorie-Seiten erstellen
python sync_to_wordpress.py --create-categories

# Term-Seiten erstellen (batch)
python sync_to_wordpress.py --create-terms --batch 50

# Vollständiger Sync
python sync_to_wordpress.py --all
```

### fix_rankmath_seo.py - SEO Optimierung

```bash
# SEO-Status analysieren
python fix_rankmath_seo.py --status

# Einzelnen Term optimieren
python fix_rankmath_seo.py --term-id 123

# Kategorie optimieren
python fix_rankmath_seo.py --category "Smart Building & IoT"

# Alle Terme optimieren
python fix_rankmath_seo.py --all --delay 2.0

# Dry Run (nur Vorschau)
python fix_rankmath_seo.py --all --dry-run
```

### generate_llms_txt.py - LLM Optimierung

```bash
# Vorschau
python generate_llms_txt.py --preview

# Dateien generieren
python generate_llms_txt.py

# Auf Server deployen
python generate_llms_txt.py --deploy
```

### progress_dashboard.py - Monitoring

```bash
# Dashboard anzeigen
python progress_dashboard.py

# Live-Modus (Updates alle 10s)
python progress_dashboard.py --watch

# Stats als JSON exportieren
python progress_dashboard.py --export stats.json
```

## Workflow

### Vollständige Glossar-Erstellung

```bash
# Phase 1: Setup
docker run -d --name profm-glossar-db ...
psql -f init.sql

# Phase 2: Generierung (ca. 2-3 Stunden)
python generate_terms.py --priority 1      # Wichtigste Terme zuerst
python generate_terms.py --all             # Restliche Terme

# Phase 3: WordPress Sync (ca. 30-45 min)
python sync_to_wordpress.py --all

# Phase 4: SEO Optimierung (ca. 1-2 Stunden)
python fix_rankmath_seo.py --all

# Phase 5: LLM Files
python generate_llms_txt.py --deploy

# Monitoring
python progress_dashboard.py --watch
```

## Kategorien

| Kategorie | Terme | Beschreibung |
|-----------|-------|--------------|
| Smart Building & IoT | 50 | Gebäudeautomation, Sensoren |
| Robotik & Automatisierung | 35 | Reinigungsroboter, Drohnen |
| Sensorik & Messtechnik | 40 | Sensoren, Monitoring |
| Gebäudetechnik (TGA) | 45 | HVAC, Elektro, Sanitär |
| Energiemanagement | 40 | Effizienz, Smart Grid |
| Sicherheitstechnik | 35 | Zutrittskontrolle, Brandschutz |
| Gebäudereinigung | 40 | Reinigungsdienste |
| Grünflächenpflege | 25 | Außenanlagen, Winterdienst |
| Catering & Services | 20 | Verpflegung, Empfang |
| CAFM & Digitalisierung | 45 | Software, BIM, Digital Twin |
| Flächenmanagement | 30 | Belegung, Workplace |
| Vertragsmanagement | 25 | SLA, Outsourcing |
| ESG & Nachhaltigkeit | 40 | CO2, Zertifizierungen |
| Predictive Maintenance | 35 | KI, Machine Learning |
| Workplace & New Work | 30 | Hybrid, Desk Sharing |

**Gesamt: 535 Fachbegriffe**

## Dateistruktur

```
glossary/
├── config.py                 # Konfiguration & Umgebungsvariablen
├── generate_terms.py         # AI Term-Generierung (GPT-4o)
├── sync_to_wordpress.py      # WordPress REST API Sync
├── fix_rankmath_seo.py       # RankMath SEO Optimierung
├── generate_llms_txt.py      # LLM-Dateien Generator
├── progress_dashboard.py     # Live-Monitoring
├── init.sql                  # PostgreSQL Schema
├── requirements.txt          # Python Dependencies
├── .env                      # Umgebungsvariablen
├── .env.example              # Template
├── data/
│   ├── categories.json       # Kategorie-Definitionen
│   └── terms_priority_1.json # Prioritäts-Terme
├── output/
│   ├── llms.txt              # Standard LLM-Datei
│   └── llms-full.txt         # Vollständige LLM-Datei
└── templates/                # DIVI Templates
```

## SEO-Features

- **RankMath Integration**: Focus Keywords, Meta Title/Description
- **600+ Wörter** pro Seite für optimale Scores
- **FAQ Schema** für Featured Snippets
- **Internal Linking** zwischen verwandten Termen
- **Schema.org** DefinedTerm Markup

## LLM-Optimierung

- **llms.txt**: Standard-Format für AI-Crawler
- **llms-full.txt**: Vollständige Wissensbasis
- **Structured Data**: JSON-LD für alle Seiten
- **API-Endpunkte**: Programmatischer Zugriff

## Geschätzte Ergebnisse

| Metrik | Ziel | Zeitraum |
|--------|------|----------|
| Indexierte Seiten | 580+ | 4-6 Wochen |
| Organischer Traffic | +50-100% | 3-6 Monate |
| Keywords Ranking | 300+ | 6 Monate |
| Featured Snippets | 20+ | 6 Monate |
| RankMath Score | 85-95 | Sofort |

## Troubleshooting

```bash
# Datenbank-Verbindung testen
psql -h localhost -p 5433 -U postgres -d profm_glossar -c "SELECT 1"

# WordPress API testen
python sync_to_wordpress.py --test

# OpenAI API testen
python generate_terms.py --test

# Logs prüfen
tail -f glossary.log
```

## Dokumentation

- [GLOSSARY_PLAN.md](./GLOSSARY_PLAN.md) - Vollständiger Implementierungsplan
- [init.sql](./init.sql) - Datenbank-Schema mit Kommentaren

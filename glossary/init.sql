-- ProFM24 Facility Management Glossar
-- Database Schema for PostgreSQL 16+
-- Website: profm24.de

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Drop existing table if exists (for development)
DROP TABLE IF EXISTS fm_glossar_terms CASCADE;
DROP VIEW IF EXISTS fm_glossar_statistics CASCADE;
DROP VIEW IF EXISTS fm_glossar_by_letter CASCADE;
DROP VIEW IF EXISTS fm_glossar_by_category CASCADE;

-- Main glossary terms table
CREATE TABLE fm_glossar_terms (
    id SERIAL PRIMARY KEY,

    -- Core term data
    term VARCHAR(255) NOT NULL UNIQUE,
    term_en VARCHAR(255),
    abbreviation VARCHAR(50),
    letter CHAR(1) NOT NULL,

    -- Content (SEO-optimized)
    definition TEXT NOT NULL CHECK (LENGTH(definition) >= 200),
    definition_short VARCHAR(500),
    examples TEXT,
    use_cases TEXT,
    benefits TEXT,

    -- Relationships
    synonyms TEXT,
    related_terms TEXT,
    parent_term_id INTEGER REFERENCES fm_glossar_terms(id),

    -- Categorization
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    tags TEXT,

    -- Target audience
    target_audience TEXT DEFAULT '["unternehmen", "immobilieneigentuemer", "hausverwaltungen"]',
    difficulty_level VARCHAR(20) DEFAULT 'intermediate' CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),

    -- SEO metadata
    slug VARCHAR(255) UNIQUE,
    meta_title VARCHAR(70),
    meta_description VARCHAR(160),
    focus_keyword VARCHAR(100),
    secondary_keywords TEXT,
    search_volume INTEGER DEFAULT 0,
    keyword_difficulty INTEGER DEFAULT 0,

    -- LLM optimization
    structured_data JSONB,
    faq_items JSONB,
    llm_context TEXT,

    -- Media
    featured_image_url TEXT,
    icon_class VARCHAR(100),
    video_url TEXT,

    -- Status & priority
    priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
    is_published BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,
    wordpress_post_id INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_fm_glossar_letter ON fm_glossar_terms(letter);
CREATE INDEX idx_fm_glossar_category ON fm_glossar_terms(category);
CREATE INDEX idx_fm_glossar_subcategory ON fm_glossar_terms(subcategory);
CREATE INDEX idx_fm_glossar_priority ON fm_glossar_terms(priority DESC);
CREATE INDEX idx_fm_glossar_published ON fm_glossar_terms(is_published);
CREATE INDEX idx_fm_glossar_featured ON fm_glossar_terms(is_featured);
CREATE INDEX idx_fm_glossar_slug ON fm_glossar_terms(slug);
CREATE INDEX idx_fm_glossar_search_volume ON fm_glossar_terms(search_volume DESC);
CREATE INDEX idx_fm_glossar_wp_id ON fm_glossar_terms(wordpress_post_id);

-- Full-text search index (German language)
CREATE INDEX idx_fm_glossar_fulltext ON fm_glossar_terms
    USING GIN(to_tsvector('german', term || ' ' || COALESCE(definition, '') || ' ' || COALESCE(synonyms, '')));

-- Trigram index for fuzzy search
CREATE INDEX idx_fm_glossar_trgm ON fm_glossar_terms
    USING GIN(term gin_trgm_ops);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_fm_glossar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_fm_glossar_timestamp
    BEFORE UPDATE ON fm_glossar_terms
    FOR EACH ROW
    EXECUTE FUNCTION update_fm_glossar_timestamp();

-- Statistics view
CREATE VIEW fm_glossar_statistics AS
SELECT
    COUNT(*) as total_terms,
    COUNT(*) FILTER (WHERE is_published) as published_terms,
    COUNT(*) FILTER (WHERE wordpress_post_id IS NOT NULL) as synced_to_wp,
    COUNT(DISTINCT letter) as letters_covered,
    COUNT(DISTINCT category) as categories_count,
    SUM(search_volume) as total_search_volume,
    ROUND(AVG(LENGTH(definition))) as avg_definition_length,
    COUNT(*) FILTER (WHERE priority = 1) as priority_1_count,
    COUNT(*) FILTER (WHERE priority = 2) as priority_2_count,
    COUNT(*) FILTER (WHERE is_featured) as featured_count
FROM fm_glossar_terms;

-- Terms by letter view
CREATE VIEW fm_glossar_by_letter AS
SELECT
    letter,
    COUNT(*) as term_count,
    json_agg(json_build_object(
        'id', id,
        'term', term,
        'slug', slug,
        'category', category,
        'priority', priority
    ) ORDER BY term) as terms
FROM fm_glossar_terms
WHERE is_published = TRUE
GROUP BY letter
ORDER BY letter;

-- Terms by category view
CREATE VIEW fm_glossar_by_category AS
SELECT
    category,
    COUNT(*) as term_count,
    SUM(search_volume) as total_search_volume,
    json_agg(json_build_object(
        'id', id,
        'term', term,
        'slug', slug,
        'priority', priority,
        'search_volume', search_volume
    ) ORDER BY priority, search_volume DESC) as terms
FROM fm_glossar_terms
WHERE is_published = TRUE
GROUP BY category
ORDER BY term_count DESC;

-- Helper function: Generate URL-safe slug
CREATE OR REPLACE FUNCTION generate_slug(input_text VARCHAR)
RETURNS VARCHAR AS $$
BEGIN
    RETURN LOWER(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(input_text, 'ä', 'ae'),
                        'ö', 'oe'),
                    'ü', 'ue'),
                'ß', 'ss'),
            '[^a-zA-Z0-9]+', '-', 'g'),
        '^-|-$', '', 'g')
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Trigger to auto-generate slug
CREATE OR REPLACE FUNCTION auto_generate_slug()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.slug IS NULL OR NEW.slug = '' THEN
        NEW.slug = generate_slug(NEW.term);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_slug
    BEFORE INSERT ON fm_glossar_terms
    FOR EACH ROW
    EXECUTE FUNCTION auto_generate_slug();

-- Insert sample terms for testing
INSERT INTO fm_glossar_terms (term, term_en, abbreviation, letter, category, definition, definition_short, examples, use_cases, benefits, synonyms, related_terms, priority, search_volume) VALUES

-- Smart Building & IoT
('Building Management System', 'Building Management System', 'BMS', 'B', 'Smart Building & IoT',
'Ein Building Management System (BMS) ist eine computergestützte Steuerungsplattform, die alle technischen Anlagen eines Gebäudes zentral überwacht, steuert und optimiert. Es integriert Heizung, Lüftung, Klimatisierung (HVAC), Beleuchtung, Sicherheitssysteme und Energiemanagement in einer einheitlichen Oberfläche. Moderne BMS nutzen IoT-Sensoren und Cloud-Technologie für Echtzeit-Monitoring und predictive Analytics.',
'Zentrale Steuerungsplattform für alle technischen Gebäudeanlagen mit IoT-Integration und Echtzeit-Monitoring.',
'In einem Bürogebäude mit 10.000 m² Fläche reduzierte ein BMS den Energieverbrauch um 25% durch automatische Anpassung der Klimatisierung an die tatsächliche Belegung.',
'Gebäudeautomation, Energieoptimierung, Predictive Maintenance, Komfortsteuerung',
'Energieeinsparung 20-30%, Reduzierte Betriebskosten, Verbesserte Luftqualität, Zentrale Steuerung, Automatische Fehlererkennung',
'Gebäudeleittechnik, GLT, Gebäudeautomationssystem, Building Automation System',
'Gebäudeleittechnik, IoT-Gateway, Smart Meter, Predictive Maintenance',
1, 2400),

('Reinigungsroboter', 'Cleaning Robot', NULL, 'R', 'Robotik & Automatisierung',
'Reinigungsroboter sind autonome oder teilautonome Maschinen, die Bodenreinigung in Gewerbe- und Industriegebäuden durchführen. Sie nutzen Lidar, Kameras und Sensoren für Navigation und Hinderniserkennung. Moderne Reinigungsroboter können Nasswischen, Kehren und Staubsaugen und arbeiten rund um die Uhr ohne menschliche Aufsicht.',
'Autonome Maschinen für die automatisierte Bodenreinigung in Gewerbegebäuden.',
'Ein Logistikzentrum mit 50.000 m² setzt 5 Reinigungsroboter ein, die nachts autonom arbeiten und die Personalkosten um 40% senken.',
'Büroreinigung, Industriereinigung, Logistik, Einzelhandel, Krankenhäuser',
'40-60% Personalkostenersparnis, 24/7 Betrieb möglich, Konstante Reinigungsqualität, Datenbasierte Optimierung, Reduzierte Arbeitsunfälle',
'Scheuersaugroboter, Bodenreinigungsroboter, Autonomous Floor Scrubber',
'Autonome Bodenreinigung, Cobot, KI-gesteuerte Reinigungsplanung',
1, 1800),

('Predictive Maintenance', 'Predictive Maintenance', 'PdM', 'P', 'Predictive Maintenance',
'Predictive Maintenance (vorausschauende Wartung) nutzt IoT-Sensoren, Machine Learning und Datenanalyse, um den optimalen Wartungszeitpunkt für Gebäudetechnik vorherzusagen. Anstatt fester Wartungsintervalle werden Anlagen gewartet, wenn Sensordaten auf bevorstehende Ausfälle hindeuten. Dies maximiert die Anlagenverfügbarkeit und minimiert ungeplante Stillstände.',
'Datenbasierte Vorhersage des optimalen Wartungszeitpunkts für Gebäudetechnik.',
'Die Aufzugsanlage eines Hochhauses nutzt Vibrationssensoren und KI, um Komponentenverschleiß zu erkennen. Ein drohender Ausfall wurde 3 Wochen vor dem tatsächlichen Defekt prognostiziert.',
'Aufzüge, HVAC-Anlagen, Pumpen, Lüftungsmotoren, Kompressoren',
'Reduzierte Ausfallzeiten um 50%, Verlängerte Anlagenlebensdauer, Optimierte Wartungskosten, Verbesserte Sicherheit, Datenbasierte Entscheidungen',
'Vorausschauende Wartung, Zustandsbasierte Instandhaltung, Condition-based Maintenance',
'Condition Monitoring, IoT-Sensoren, Machine Learning, MTBF',
1, 3200),

('CAFM-Software', 'CAFM Software', 'CAFM', 'C', 'CAFM & Digitalisierung',
'Computer Aided Facility Management (CAFM) Software ist eine Anwendung zur digitalen Verwaltung aller Facility-Management-Prozesse. Sie umfasst Flächenmanagement, Instandhaltungsplanung, Inventarverwaltung, Vertragsmanagement und Reporting. Moderne CAFM-Systeme bieten Cloud-Hosting, mobile Apps und Schnittstellen zu BIM, ERP und IoT-Systemen.',
'Digitale Plattform zur Verwaltung aller Facility-Management-Prozesse.',
'Eine Hausverwaltung mit 50 Objekten nutzt CAFM zur zentralen Steuerung aller Wartungsaufträge. Die Reaktionszeit bei Störungen sank um 60%.',
'Flächenmanagement, Wartungsplanung, Inventar, Umzugsplanung, Reporting',
'Zentrale Datenhaltung, Automatisierte Workflows, Transparente Prozesse, Mobile Verfügbarkeit, Rechtssichere Dokumentation',
'Facility Management Software, FM-Software, Gebäudemanagement-Software',
'BIM, IWMS, Ticketing-System, Digitaler Gebäudepass',
1, 2900),

('ESG-Reporting', 'ESG Reporting', 'ESG', 'E', 'ESG & Nachhaltigkeit',
'ESG-Reporting (Environmental, Social, Governance) ist die systematische Erfassung und Berichterstattung von Nachhaltigkeitskennzahlen für Immobilien. Im Facility Management umfasst dies CO2-Emissionen, Energieverbrauch, Wassernutzung, Abfallmanagement und soziale Faktoren. Die EU-Taxonomie und CSRD verpflichten viele Unternehmen zu standardisiertem ESG-Reporting.',
'Systematische Erfassung und Berichterstattung von Nachhaltigkeitskennzahlen für Gebäude.',
'Ein Gewerbeimmobilienportfolio mit 20 Objekten implementierte automatisiertes ESG-Reporting und verbesserte sein GRESB-Rating von 2 auf 4 Sterne.',
'Jahresberichte, Investoren-Reporting, EU-Taxonomie, GRESB, Nachhaltigkeitszertifizierung',
'Verbesserte ESG-Ratings, Zugang zu grüner Finanzierung, Regulatorische Compliance, Transparenz für Stakeholder, Wettbewerbsvorteil',
'Nachhaltigkeitsberichterstattung, Sustainability Reporting, CSR-Reporting',
'CO2-Fußabdruck, EU-Taxonomie, GRESB, CRREM-Pfad',
1, 2100);

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON fm_glossar_terms TO profm_user;
-- GRANT USAGE, SELECT ON SEQUENCE fm_glossar_terms_id_seq TO profm_user;

-- Show statistics after setup
SELECT '=== ProFM24 Glossar Database Initialized ===' as status;
SELECT * FROM fm_glossar_statistics;

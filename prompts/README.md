# Claude Code Prompts - WordPress Management

Prompturi personalizate pentru administrarea site-urilor WordPress cu focus pe:
- **Traduceri** (EN→DE) cu OpenAI GPT-4o
- **SEO** cu DataForSEO și RankMath Pro
- **Content Management** și optimizare

## Structură

```
prompts/
├── translation/          # Prompturi pentru traduceri EN→DE
│   ├── base.md          # Prompt de bază pentru traduceri
│   ├── pages.md         # Traducere pagini
│   ├── posts.md         # Traducere articole
│   └── seo-meta.md      # Traducere meta SEO
├── seo/                  # Prompturi pentru SEO
│   ├── audit.md         # Audit SEO complet
│   ├── keywords.md      # Cercetare keywords
│   ├── rankmath.md      # Optimizare RankMath
│   └── dataforseo.md    # Integrare DataForSEO
├── sites/                # Prompturi per site
│   ├── gebaudereinigung-buchholz.md
│   ├── hamburger-gebaeudereinigung24.md
│   ├── reinigungsdienstleistungen.md
│   ├── profm24.md
│   ├── north-cleaning.md
│   ├── avi-med.md
│   └── studymedicine24.md
└── workflows/            # Fluxuri de lucru complete
    ├── new-page.md      # Flux creare pagină nouă
    ├── translate-optimize.md  # Traducere + SEO
    └── monthly-audit.md # Audit lunar
```

## Utilizare

Fiecare prompt poate fi încărcat în Claude Code pentru task-uri specifice:

```bash
# Exemplu: Traducere pagină
cat prompts/translation/pages.md | claude

# Exemplu: Audit SEO
cat prompts/seo/audit.md | claude
```

## Site-uri Gestionate

| Site | Domeniu | Focus |
|------|---------|-------|
| Gebäudereinigung Buchholz | gebäudereinigung-buchholz.de | Traduceri EN→DE, SEO local |
| Hamburger Gebäudereinigung | hamburger-gebaeudereinigung24.de | SEO local Hamburg |
| Reinigung Dienstleistungen | reinigungsdienstleistungen.com | SEO național DE |
| Pro-FM | profm24.de | Facility Management, SEO B2B |
| North Cleaning | north-cleaning.de | eCommerce, SEO |
| Avi Med | avi-med.com | Medical, SEO internațional |
| StudyMedicine | studymedicine24.com | Education, SEO internațional |

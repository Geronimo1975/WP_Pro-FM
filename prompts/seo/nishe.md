## Task: Configurare structură SEO pentru toate submodulele WP-ADMIN

### Cerință
Pentru fiecare submodul din WP-ADMIN, creează/actualizează directorul `SEO/` cu configurația:

1. **Fișier `config.json`** cu:
   - `geolocation`: țară/oraș target (ex: "Germany/Hamburg")
   - `language`: limba principală (de/en)
   - `niche`: domeniul de activitate
   - `keywords`: array cu 50 cuvinte cheie relevante pentru ranking

2. **Acțiuni necesare**:
   - Verifică existența `SEO/` în fiecare submodul
   - Dacă există → actualizează cu structura standard
   - Dacă nu există → creează directorul și fișierele

### Submodule și detalii business:
| Submodul | Website | Nișă | Locație |
|----------|---------|------|---------|
| WP_Pro-FM | profm24.de | Facility Management | Germany |
| WP_Gebaudereinigung-Buchholz | gebäudereinigung-buchholz.de | Cleaning Services | Buchholz, Germany |
| WP_north-cleaning | north-cleaning.de | Cleaning Services | North Germany |
| WP-StudyMedicine_24 | studymedicine24.com | Medical Education | International |
| WP_Hamburger-geneudereinigung24 | hamburger-gebaeudereinigung24.de | Cleaning Services | Hamburg |
| WP_Avi_Med | avi-med.com | Medical | Germany |
| WP_ReinigungDistleistungen | reinigungsdienstleistungen.com | Cleaning Services | Germany |

### Output așteptat
Pentru fiecare submodul: `SEO/config.json` cu 50 keywords optimizate pentru nișa și geolocația specifică.

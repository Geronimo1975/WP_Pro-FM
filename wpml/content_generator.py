"""
German Content Generator for WordPress with WPML
Generates SEO-optimized content in German for Facility Management
"""

import os
from typing import Optional, Dict, List
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class GermanContentGenerator:
    """Generate German content for Facility Management website"""

    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"

        # Facility Management services in German
        self.services = [
            "Gebäudereinigung",
            "Büroreinigung",
            "Fensterreinigung",
            "Grundreinigung",
            "Unterhaltsreinigung",
            "Industriereinigung",
            "Teppichreinigung",
            "Fassadenreinigung",
            "Winterdienst",
            "Grünflächenpflege",
            "Hausmeisterservice",
            "Facility Management"
        ]

        # German cities for local SEO
        self.cities = [
            "Berlin", "Hamburg", "München", "Köln", "Frankfurt",
            "Stuttgart", "Düsseldorf", "Leipzig", "Dortmund", "Essen",
            "Bremen", "Dresden", "Hannover", "Nürnberg", "Duisburg"
        ]

    def generate_blog_post(self, topic: str, target_keyword: str,
                           word_count: int = 800,
                           include_faq: bool = True) -> Dict[str, str]:
        """Generate a complete blog post in German"""

        prompt = f"""Erstelle einen professionellen Blog-Artikel auf Deutsch für eine Facility Management Firma.

THEMA: {topic}
HAUPTKEYWORD: {target_keyword}
WORTANZAHL: ca. {word_count} Wörter

ANFORDERUNGEN:
1. SEO-optimiert mit dem Hauptkeyword natürlich eingebaut (Keyword-Dichte ~1.5%)
2. Professioneller, vertrauenswürdiger Ton
3. Strukturiert mit H2 und H3 Überschriften
4. Praktische Tipps und Mehrwert für den Leser
5. Call-to-Action am Ende
{"6. FAQ-Sektion mit 3-4 häufigen Fragen am Ende" if include_faq else ""}

FORMAT (wichtig - exakt einhalten):
---TITLE---
[Einprägsamer SEO-Titel mit Keyword, max 60 Zeichen]

---META_DESCRIPTION---
[Meta-Beschreibung, 150-160 Zeichen, mit Keyword]

---CONTENT---
[Der vollständige Artikel im HTML-Format mit <h2>, <h3>, <p>, <ul>, <li> Tags]

---EXCERPT---
[Kurze Zusammenfassung, 2-3 Sätze]

---FOCUS_KEYWORD---
{target_keyword}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Du bist ein erfahrener deutscher Content-Writer spezialisiert auf B2B Facility Management und Gebäudereinigung. Schreibe professionell, informativ und SEO-optimiert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )

        content = response.choices[0].message.content
        return self._parse_generated_content(content)

    def generate_service_page(self, service: str, city: Optional[str] = None) -> Dict[str, str]:
        """Generate a service page in German, optionally localized for a city"""

        location_text = f" in {city}" if city else ""
        keyword = f"{service}{location_text}"

        prompt = f"""Erstelle eine professionelle Service-Seite auf Deutsch für:

SERVICE: {service}
{"STADT: " + city if city else "DEUTSCHLAND-WEIT"}

ANFORDERUNGEN:
1. Überzeugende Verkaufsseite für B2B-Kunden
2. Beschreibe den Service detailliert
3. Vorteile und USPs hervorheben
4. Vertrauenssignale (Erfahrung, Qualität, Zuverlässigkeit)
5. Lokale Relevanz{"für " + city if city else ""}
6. Klare Call-to-Actions

FORMAT (exakt einhalten):
---TITLE---
[SEO-Titel mit Service{" und Stadt" if city else ""}, max 60 Zeichen]

---META_DESCRIPTION---
[Meta-Beschreibung, 150-160 Zeichen]

---CONTENT---
[Vollständiger Seiteninhalt im HTML-Format]

---EXCERPT---
[Kurze Beschreibung für Übersichten]

---FOCUS_KEYWORD---
{keyword}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Du bist ein erfahrener deutscher Copywriter für Facility Management Unternehmen. Schreibe überzeugend, professionell und verkaufsorientiert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        return self._parse_generated_content(response.choices[0].message.content)

    def generate_faq(self, topic: str, num_questions: int = 5) -> List[Dict[str, str]]:
        """Generate FAQ items in German"""

        prompt = f"""Erstelle {num_questions} häufig gestellte Fragen (FAQ) auf Deutsch zum Thema:

THEMA: {topic}

Für jede Frage:
- Realistische Kundenfrage
- Informative, hilfreiche Antwort (2-4 Sätze)
- SEO-relevant

FORMAT (JSON):
[
  {{"question": "Frage 1?", "answer": "Antwort 1"}},
  {{"question": "Frage 2?", "answer": "Antwort 2"}}
]
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Du bist ein Experte für Facility Management in Deutschland. Antworte im JSON-Format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        import json
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            content = response.choices[0].message.content
            start = content.find('[')
            end = content.rfind(']') + 1
            if start != -1 and end != 0:
                return json.loads(content[start:end])
            return []

    def translate_content(self, content: str, source_lang: str = 'en',
                          target_lang: str = 'de') -> str:
        """Translate content to German while maintaining HTML structure"""

        prompt = f"""Übersetze den folgenden Text von {source_lang} nach {target_lang}.

WICHTIG:
- Behalte alle HTML-Tags exakt bei
- Übersetze nur den Text, nicht die Tags
- Natürliche, professionelle deutsche Sprache
- Fachbegriffe korrekt übersetzen

TEXT:
{content}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Du bist ein professioneller Übersetzer spezialisiert auf Facility Management und technische Texte."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3000
        )

        return response.choices[0].message.content

    def _parse_generated_content(self, content: str) -> Dict[str, str]:
        """Parse the generated content into structured format"""
        result = {
            'title': '',
            'meta_description': '',
            'content': '',
            'excerpt': '',
            'focus_keyword': ''
        }

        sections = {
            '---TITLE---': 'title',
            '---META_DESCRIPTION---': 'meta_description',
            '---CONTENT---': 'content',
            '---EXCERPT---': 'excerpt',
            '---FOCUS_KEYWORD---': 'focus_keyword'
        }

        current_section = None
        current_content = []

        for line in content.split('\n'):
            line_stripped = line.strip()
            if line_stripped in sections:
                if current_section:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = sections[line_stripped]
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            result[current_section] = '\n'.join(current_content).strip()

        return result


if __name__ == '__main__':
    generator = GermanContentGenerator()

    # Test: Generate a blog post
    print("Generating German blog post...")
    post = generator.generate_blog_post(
        topic="Vorteile professioneller Büroreinigung für Unternehmen",
        target_keyword="professionelle Büroreinigung",
        word_count=600
    )

    print(f"\nTitle: {post['title']}")
    print(f"Meta: {post['meta_description']}")
    print(f"Keyword: {post['focus_keyword']}")
    print(f"\nContent preview:\n{post['content'][:500]}...")

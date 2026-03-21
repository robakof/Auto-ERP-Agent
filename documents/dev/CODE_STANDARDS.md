# Code Standards — domain pack

Standardy kodowania ładowane gdy Developer pisze lub recenzuje kod.
Nie ładuj przy przetwarzaniu suggestions ani planowaniu architektury.

---

## Nazewnictwo

Opisowe, jednoznaczne nazwy:
- `database_config` zamiast `config`
- `validate_user_email` zamiast `validate`
- Nazwa zawiera "and" lub "or" → prawdopodobnie robi za dużo

Bez temporal naming:
- `query` zamiast `query_new` — w przyszłości nie będzie "alternatywy"

Konwencje językowe:
- Python: `snake_case` funkcje/zmienne, `PascalCase` klasy
- JavaScript: `camelCase` funkcje/zmienne, `PascalCase` klasy
- Stałe: `UPPER_SNAKE_CASE`

---

## Struktura funkcji

Idealna funkcja: 5-20 linii.
- Jedna odpowiedzialność
- Deterministyczna (ten sam input → ten sam output)

---

## Modularność

Jeden plik = jedna odpowiedzialność. Preferuj 100-300 linii na plik.

- DRY — brak duplikacji kodu
- Single Responsibility — jeden moduł = jedna odpowiedzialność
- Loose coupling — zmiany w module A nie wymagają zmian w module B

---

## Projektowanie baz danych

Przed `CREATE TABLE` napisz 5 przykładowych `INSERT`-ów dla różnych przypadków użycia.
Jeśli przykłady nie pasują do schematu — schemat jest zły.

Schemat DB to decyzja o rozumieniu domeny, nie decyzja techniczna.

---

## Samodokumentujący się kod

Kod czytelny bez komentarzy:
- Jasne nazwy funkcji i zmiennych
- Type hints dla publicznych funkcji
- Docstrings dla publicznych funkcji

Komentarze tylko "dlaczego", nie "co":
- Obejścia bugów
- Nieintuicyjne decyzje biznesowe
- Złożone algorytmy wymagające kontekstu

---

## Error handling

- Walidacja inputów (szczególnie user input)
- Obsługa błędów sieciowych
- Timeouty dla external calls
- Graceful degradation

---

## Bezpieczeństwo

- Sekrety (API keys, hasła, tokeny) → zmienne środowiskowe, nie kod
- Waliduj i sanityzuj input użytkownika (SQL injection, XSS)
- Principle of Least Privilege — minimalne uprawnienia

---

## Logowanie

- Structured logging (nie `print()`)
- Odpowiedni poziom: DEBUG, INFO, WARNING, ERROR
- Loguj kontekst, nie tylko komunikaty

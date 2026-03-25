# Research: Konwencje komunikacji agent-agent w systemach multi-agent

## Kontekst

System wieloagentowy z 6 wyspecjalizowanymi rolami komunikuje się przez wspólną bazę danych (SQLite). Agenci wysyłają wiadomości do innych ról, zgłaszają obserwacje/sugestie, przekazują zadania do backlogu i eskalują do człowieka. Problem: sugestii przybywa szybciej niż system je absorbuje (176 otwartych), wiadomości nie mają ustandaryzowanego formatu, brakuje kategoryzacji i mechanizmów zapobiegania duplikatom.

**Czego NIE rób:** Nie oceniaj czy nasze obecne podejście jest dobre ani jak dopasować konwencję do projektu. To osobny krok po badaniu.

## Pytania badawcze

1. **Standardy formatu wiadomości w MAS:** Jak dojrzałe systemy multi-agent (JADE, FIPA ACL, KQML, AutoGen, CrewAI) standaryzują format wiadomości między agentami? Jakie pola uznają za obowiązkowe?

2. **Ontologie komunikacji i speech acts:** Jakie ontologie komunikacji agent-agent istnieją (speech acts, performatives, FIPA communicative acts)? Które kategorie wiadomości są naprawdę użyteczne w praktyce, a które to over-engineering?

3. **Zarządzanie backlogiem obserwacji/sugestii:** Jak duże projekty zarządzają rosnącym backlogiem obserwacji od wielu agentów? Strategie: TTL (auto-expire), priority decay, batch triage, dedup? Co działa w praktyce?

4. **Anti-patterns w komunikacji agent-agent:** Jakie wzorce komunikacji między agentami powodują szum, duplikaty lub utratę ważnych informacji? Co jest empirycznie udokumentowane jako szkodliwe?

## Output contract

Zapisz wyniki do: `documents/researcher/research/research_results_convention_communication.md`

Struktura (obowiązkowa):
- **TL;DR** — 3-5 najważniejszych wniosków z siłą dowodów
- **Wyniki per pytanie** — każde pytanie osobno, siła dowodów per wniosek (empiryczne / praktyczne / spekulacja)
- **Otwarte pytania / luki** — czego nie udało się potwierdzić lub gdzie źródła się rozjeżdżają
- **Źródła** — tytuł, URL, opis zastosowania

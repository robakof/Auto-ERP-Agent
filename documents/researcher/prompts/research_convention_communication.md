# Research: Operacyjny protokół komunikacji agent-agent

## Kontekst

Projekt Mrowisko ma 176 open suggestions — agenci generują obserwacje szybciej niż system je absorbuje. Root cause: brak operacyjnej konwencji komunikacji. Mamy research o wzorcach architektonicznych (Blackboard, Tuple Space, Stigmergy) — nie powtarzaj tego. Potrzebujemy niższy poziom: format wiadomości, kategoryzacja, anti-duplikacja.

Nasz system: SQLite DB (mrowisko.db), agent_bus_cli.py z komendami: send, suggest, backlog-add, flag, handoff. Typy sugestii: rule, discovery, observation, tool.

## Pytania badawcze

1. **Message taxonomies w multi-agent systems:** Jak dojrzałe systemy MAS (JADE/FIPA, AutoGen, CrewAI) kategoryzują wiadomości? Jakie taksonomie speech acts / performatives stosują? Które kategorie są naprawdę potrzebne vs które to over-engineering?

2. **Anti-duplikacja obserwacji:** Jak systemy z wieloma agentami radzą sobie z duplikatami obserwacji? Mechanizmy: dedup by similarity, canonical IDs, merge strategies? Czy LLM-based dedup jest praktyczny?

3. **Suggestion/observation overflow:** Jak projekty zarządzają rosnącym backlogiem sugestii/obserwacji? Strategie: TTL (auto-expire), priority decay, batch processing, triage workflows? Co działa w praktyce?

4. **Message format standards:** Jakie formaty wiadomości agent-agent są najskuteczniejsze? (structured vs freeform, mandatory fields, max length, severity levels). Jak balansować strukturę (machine-parseable) z elastycznością (agent musi móc opisać niuans)?

5. **Inbox management patterns:** Jak systemy multi-agent zarządzają inbox overflow? Read/unread, priority sorting, auto-routing, attention management?

## Output contract

Zapisz wyniki do: `documents/researcher/research/convention_communication.md`

Struktura:
- TL;DR — 3-5 kluczowych wniosków
- Wyniki per pytanie (z siłą dowodów)
- Otwarte pytania / luki
- Źródła

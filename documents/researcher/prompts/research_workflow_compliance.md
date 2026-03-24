# Research: Optymalizacja dokumentów workflow w systemach wieloagentowych

## Pytania badawcze

1. **Compliance przez strukturę dokumentu** — jakie techniki sprawdzają się przy pisaniu
   instrukcji workflow dla LLM żeby agent nie pomijał kroków? Czy istnieją ustalone wzorce
   (np. checklist zamiast prozy, explicit gates, "nie kontynuuj dopóki...")?

2. **Separacja dokumentów** — czy lepiej trzymać workflow w dokumencie roli (agent-centric)
   czy w osobnym dokumencie workflow (process-centric, współdzielony między rolami)?
   Jakie są trade-offy przy multi-agent handoffach?

3. **Phase gates w promptach** — jak wymuszać sekwencyjność kroków przez samą strukturę
   promptu, zanim wprowadzi się narzędzia egzekwujące? Czy istnieje wzorzec "mini-protocol"
   per faza?

4. **Długość vs. precyzja** — jak skrócić dokument workflow bez utraty compliance?
   Czy krótsze prompty dają lepsze wyniki czy gorsze?

5. **Wzorce z produkcji** — co mówią zespoły budujące agentowe systemy produkcyjne
   (Anthropic, LangChain, CrewAI, AutoGen) o strukturze promptów workflow?

## Kontekst projektu

System wieloagentowy: ERP Specialist + Analityk + Developer. Workflow tworzenia widoków BI
ma 4 fazy z handoffami między rolami. Problem: agenci pomijają kroki (brak eksportu,
zatwierdzenie bez weryfikacji). Szukamy wzorców dokumentacyjnych + decyzji architektonicznej
(workflow w folderze agenta vs. osobny folder `workflows/`).

## Plik odpowiedzi

Zapisz wyniki do: `documents/methodology/research_results_workflow_compliance.md`

Struktura odpowiedzi:
- Kluczowe wzorce (z nazwami i źródłami)
- Rekomendacja ws. separacji dokumentów (agent-centric vs. process-centric)
- Konkretne techniki do zastosowania w naszym workflow
- Co NIE działa (jeśli jest takie info)

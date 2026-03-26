# Analiza workflow człowieka — wzorce do przejęcia przez PM

*Data: 2026-03-26*
*Autor: Architect*
*Źródło: 1570 wiadomości z tabeli conversation (speaker=human)*

---

## Odkryte wzorce

### Kategorie wiadomości człowieka

| Kategoria | Liczba | % | PM przejmie? |
|---|---|---|---|
| Wskazanie roli / kontekst sesji | 295 | 19% | Częściowo (PM routuje) |
| Wiadomości strategiczne (>200 znaków) | 283 | 18% | ✗ (wymaga człowieka) |
| Sprawdzanie stanu (inbox, backlog) | 185 | 12% | ✓ |
| Routing wiadomości ("masz wiadomość") | 102 | 7% | ✓ |
| Routing researchy | 73 | 5% | ✓ |
| Zatwierdzenia ("tak", "ok", "realizuj") | 66 | 4% | Częściowo (approval gate) |
| Testowanie manualne | 41 | 3% | ✗ (wymaga człowieka) |
| Korekty ("cofnij", "źle") | 35 | 2% | ✗ (wymaga człowieka) |

### Cykl pracy człowieka (dispatcher loop)

```
1. Uruchom agenta (wybierz rolę, wpisz kontekst)
2. Agent pracuje → daje handoff/wynik
3. Przełącz terminal do innej roli
4. Powiedz "Masz wiadomość od X" / "Research wrócił"
5. Agent czyta, pracuje
6. Czekaj lub przełącz do następnego
7. Powtórz
```

Kroki 3-4-6 to rutyna do automatyzacji przez PM v1.

### Narzędzia zidentyfikowane jako potrzebne

| Narzędzie | Status | Priorytet |
|---|---|---|
| `inbox-summary` | Zlecone Dev (#388) | Must — PM v1 |
| `live-agents` | Zlecone Dev (#388) | Must — PM v1 |
| `handoffs-pending` | Zlecone Dev (#388) | Must — PM v1 |
| `read_transcript.py` (tools/) | PoC w tmp/ | Should — PM v2 |

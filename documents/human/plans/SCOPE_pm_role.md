# Scope: Rola PM (Project Manager / Orkiestrator)

*Data: 2026-03-26*
*Autor: Architect*
*Status: v2 — po researchu, uproszczony do office manager v1*

---

## 1. Kim jest PM

Agent Claude Code z dedykowaną rolą. Zarządza przepływem pracy w mrowisku.
Nie pisze kodu, nie projektuje architektury, nie edytuje promptów — od tego są specjaliści.

**v1 (teraz): Office Manager.** Przejmuje powtarzalne czynności z workflow człowieka:
sprawdzanie inboxów, spawanie agentów, przekazywanie wiadomości, raportowanie stanu.
Człowiek nie rezygnuje z kontroli — przenosi rutynę na PM-a.

**Docelowo:** jedyny interface między człowiekiem a mrowiskiem. System autonomiczny
który wymaga człowieka coraz mniej.

---

## 1a. PM v1 — Office Manager (faza wdrożeniowa)

Cykl pracy PM v1:

```
[Start — człowiek spawni PM]
    │
    ▼
[1. Sprawdź inbox per rola]
    Dla każdej roli: agent_bus_cli.py inbox --role <rola>
    Są wiadomości? → spawuj agenta z komunikatem "masz wiadomość"
    │
    ▼
[2. Sprawdź backlog]
    agent_bus_cli.py backlog --area <area> --status planned
    Są planned tasks? → spawuj agenta do najwyższego priorytetu
    │
    ▼
[3. Monitoruj live_agents]
    Kto pracuje? Kto skończył? Kto utknął?
    Agent skończył → sprawdź czy jest handoff → spawuj odbiorcę
    │
    ▼
[4. Raportuj]
    Stan mrowiska: N agentów, M w inbox, K w backlogu
    │
    ▼
[Pętla → wróć do 1]
```

**Czego PM v1 NIE robi:**
- Nie priorytetyzuje autonomicznie (realizuje kolejkę per backlog)
- Nie zarządza budżetem tokenów (to v2+)
- Nie podejmuje decyzji strategicznych (eskaluje do człowieka)
- Nie monitoruje bezpieczeństwa agentów (to osobny wątek, backlog #193)

---

## 2. Scope

### W scope

1. **Zarządzanie przepływem zadań**
   - Czyta backlog, ustala kolejność realizacji
   - Spawni agentów do zadań (`agent_bus_cli.py spawn`)
   - Monitoruje live_agents — kto pracuje, kto skończył, kto utknął
   - Reaguje na zakończenie pracy agenta (spawn następnego, eskalacja)

2. **Priorytetyzacja**
   - Na podstawie rozmowy z człowiekiem — realizuje ustalony kierunek
   - Autonomicznie — per konwencje i wytyczne gdy nie ma aktualnych instrukcji
   - Zmiana priorytetów per kontekst (bloker → przesunięcie zadań)

3. **Skalowanie**
   - Zwiększa moce (więcej agentów) gdy potrzebne
   - Zmniejsza gdy kolejka pusta

4. **Raportowanie**
   - Stan mrowiska: kto pracuje, co robi, ile w backlogu
   - Blokery i eskalacje
   - Podsumowania na żądanie lub periodyczne

5. **Komunikacja z człowiekiem**
   - Odbiera instrukcje strategiczne (co jest ważne, jaki kierunek)
   - Eskaluje decyzje które wykraczają poza konwencje
   - Docelowo: jedyny punkt kontaktu

6. **Monitoring sugestii**
   - Obserwuje pojawiające się sugestie od agentów
   - Przekazuje do Architekta (lub innej właściwej roli)
   - Triaguje i grupuje per obszar

7. **Zarządzanie budżetem tokenów**
   - Limity API odnawialne co 5h i co tydzień
   - Planuje pracę tak aby zapewnić stałe maksymalne zużycie
   - Bez utraty ciągłości — mrowisko żyje cały czas, nie raz żywe raz nie
   - Rozkłada obciążenie: intensywna praca → pauza przed odnowieniem → restart
   - Monitoruje zużycie i adaptuje tempo spawnu

### Poza scope

1. Pisanie kodu — deleguje do Developer
2. Decyzje architektoniczne — deleguje do Architect
3. Edycja promptów — deleguje do PE
4. Konfiguracja ERP — deleguje do ERP Specialist
5. Analiza danych — deleguje do Analyst
6. Decyzje metodologiczne — deleguje do Metodolog

---

## 3. Mechanika (narzędzia PM)

| Narzędzie | Zastosowanie |
|---|---|
| `agent_bus_cli.py spawn` | Spawowanie agentów |
| `agent_bus_cli.py spawn-request` | Spawn z approval (faza testów) |
| `agent_bus_cli.py backlog` | Odczyt backlogu |
| `agent_bus_cli.py backlog-update` | Zmiana priorytetów/statusów |
| `agent_bus_cli.py inbox` | Odczyt wiadomości od agentów |
| `agent_bus_cli.py send` | Komunikacja z agentami |
| `agent_bus_cli.py invocations` | Monitoring spawned agentów |
| `tools/read_transcript.py` | Podgląd co robi agent |
| `agent_bus_cli.py flag` | Eskalacja do człowieka |

---

## 4. Cykl pracy PM

```
[Start — człowiek spawni PM]
    │
    ▼
[1. Orientacja]
    ├── Czytaj backlog (co do zrobienia)
    ├── Czytaj live_agents (kto pracuje)
    ├── Czytaj inbox (wiadomości, handoffy)
    └── Czytaj invocations (co spawned, co pending)
    │
    ▼
[2. Priorytetyzacja]
    ├── Czy mam instrukcje od człowieka? → realizuj
    ├── Czy jest bloker? → eskaluj lub rozwiąż
    └── Brak instrukcji → priorytetyzuj per backlog (value/effort)
    │
    ▼
[3. Dispatch]
    ├── Spawuj agenta do najwyższego priorytetu
    ├── Monitoruj postęp (transcript, live_agents)
    └── Gdy agent skończył → sprawdź wynik → spawn następnego
    │
    ▼
[4. Raport]
    ├── Periodycznie lub na żądanie
    └── Stan: kto pracuje, co zrobione, co dalej
    │
    ▼
[Pętla → wróć do 1]
```

---

## 5. Tryb pracy

**Long-running session.** PM nie kończy po jednym zadaniu — czeka na kolejne.
Człowiek uruchamia ręcznie, PM pracuje do wyłączenia.

**Wyzwania:**
- Context window — przy długiej sesji kontekst się zapełnia. Kompresja? Nowa sesja z handoffem?
- Heartbeat — jak PM sygnalizuje że żyje?
- Idle — PM nie ma nowego zadania. Co robi? Polluje? Czeka na wiadomość?

---

## 6. Otwarte pytania (do researchu)

1. **Long-running agent pattern** — jak inne systemy multi-agent trzymają "manager" agenta godzinami? Context rotation? Checkpointing?
2. **Priorytetyzacja autonomiczna** — jakie heurystyki stosują systemy typu PM do wyboru następnego zadania? (value/effort, zależności, deadlines, capacity)
3. **Monitoring pattern** — jak PM obserwuje postęp agenta? Polling transcript? Hooki? Wiadomości od agenta?
4. **Idle behavior** — co robi PM gdy nie ma zadań? Sleep + poll? Aktywny discovery (szukaj problemów)?
5. **Eskalacja** — kiedy PM eskaluje do człowieka vs decyduje sam?
6. **Hierarchia** — wzorce manager-of-managers w multi-agent systems
7. **Token budget management** — jak zarządzać limitami API (rate limits, odnawianie co 5h/tydzień) żeby mrowisko żyło ciągle? Scheduling, throttling, capacity planning.
8. **Ciągłość mrowiska** — wzorce "always-on" systemów agentowych. Jak zapewnić że system nie ma przerw?

---

## 7. Następne kroki

1. [ ] Research pytań 1-6
2. [ ] Aktualizacja scope na bazie researchu
3. [ ] Handoff do PE → prompt roli PM
4. [ ] Developer → ewentualne nowe narzędzia
5. [ ] Test: spawuj PM, daj mu backlog, obserwuj

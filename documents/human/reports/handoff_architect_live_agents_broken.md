# Handoff do Architekta: live_agents — fundamentalnie zepsuty

**Od:** Developer
**Data:** 2026-03-29
**Priorytet:** Blokujący — bez wiarygodnego stanu agentów nie można budować resume, poke, stop ani dashboardu

---

## Stan faktyczny

DB mówi że żyją 3 agenci. W rzeczywistości żyje 1 (ja — developer). System nie widzi:
- **Mnie** — moja sesja (claude_uuid `cd2bb132`) jest `stopped` (record #46), a mój heartbeat aktualizuje **rekord analityka** (#34)
- **Martwego analityka** — record #34 jest `active` bo mój heartbeat go ożywia
- **Martwego PE** — record #27 jest `active` bo nikt go nie zamknął (brak GC)
- **Martwego developer spawn** — record #47 jest `starting` wiecznie (nigdy nie wystartował)

## Dowód — ślad tożsamości

```
Record #34 (analyst):
  session_id:      46171434a65b       ← mrowisko session analityka
  role:            analyst
  claude_uuid:     4480d46b           ← claude_uuid ANALITYKA z testu spawn
  transcript_path: cd2bb132...jsonl   ← MÓJ transcript developera!
  last_activity:   13:16:29           ← MÓJ heartbeat (jestem jedyną żywą sesją)
  status:          active             ← FAŁSZ — analityk nie żyje

Record #46 (developer):
  session_id:      cd2bb132           ← mój prawdziwy claude_uuid
  role:            developer
  claude_uuid:     NULL               ← nigdy nie ustawiony
  status:          stopped            ← FAŁSZ — ja żyję!
```

## 7 zidentyfikowanych bugów

### B1: uuid_bridge jest role-blind
`session_init` claimuje DOWOLNY unclaimed uuid z bridge niezależnie od roli.
Developer może przejąć uuid analityka → resume do sesji analityka.

**Kod:** `session_init.py:218` — `SELECT ... WHERE session_id IS NULL ORDER BY id DESC LIMIT 1`

### B2: uuid_bridge jest non-deterministic
"ORDER BY id DESC LIMIT 1" = ostatni insert wygrywa. W multi-session kilka uuid
ląduje w bridge jednocześnie → session_init jednej roli łapie uuid innej.

### B3: Heartbeat ghost
Raz przypisany zły `claude_uuid` powoduje że heartbeat (on_user_prompt:60-65)
aktualizuje CUDZY rekord live_agents. Mój developer heartbeat ożywia martwego analityka.

**Kod:** `on_user_prompt.py:60` — `UPDATE live_agents SET last_activity WHERE claude_uuid = ?`

### B4: Brak heartbeat timeout / GC
Nie ma mechanizmu oznaczającego sesje jako `stopped` gdy heartbeat milknie.
View `v_agent_status` rozróżnia "working" vs "stale" ale nigdy nie przechodzi do "stopped".
Martwe sesje zostają "active" na zawsze.

### B5: Resume path reactivuje złą rolę
session_init w ścieżce RESUME (linia 234-248) nie sprawdza czy znaleziony rekord
ma tę samą rolę. Developer "wznawia" sesję analityka → rola w rekordzie zostaje `analyst`.

### B6: Spawn → Claude Code session mismatch
Spawner tworzy rekord z losowym UUID jako session_id. Claude Code startuje z INNYM
session_id (claude_uuid). Łączenie przez uuid_bridge jest post-hoc i zawodne (B1, B2).

### B7: Dwa systemy tożsamości luźno spojone
- mrowisko session_id (krótki hash z session_init)
- claude_uuid (UUID z Claude Code)
Połączone przez uuid_bridge bez gwarancji integralności. Jedno źródło prawdy nie istnieje.

## Pytanie do Architekta

Proponuję zaprojektować od nowa, nie łatać. Kluczowe pytania:

1. **Jedno ID czy dwa?** Czy mrowisko powinno używać claude_uuid jako primary ID
   (eliminując uuid_bridge)? Czy claude_uuid jest stabilne na /resume?

2. **Heartbeat timeout → auto-stop.** Np. `last_activity > now - 10 min` → `stopped`.
   Kto to robi? Cron? Hook? Extension poll?

3. **Spawn → session link.** Jak deterministycznie połączyć spawn record z Claude Code
   session? Opcje: terminal_name matching, file-based rendezvous, spawner czeka na session_init.

4. **Role isolation.** uuid_bridge musi wiedzieć dla jakiej roli jest claim.
   Albo: eliminacja bridge, identyfikacja po terminal_name.

## Co dalej

Czekam na decyzję architektoniczną zanim dotykam kodu. Obecne łatki (uuid_bridge, heartbeat fix)
nie naprawiają fundamentu — każdy fix ujawnia kolejny race condition.

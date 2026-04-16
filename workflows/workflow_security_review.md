---
workflow_id: security_review
version: "1.0"
owner_role: security_specialist
trigger: "Architect konczy code review z wynikiem PASS — kod gotowy do security review"
participants:
  - developer (autor kodu)
  - architect (code review PASS)
  - security_specialist (security reviewer)
related_docs:
  - documents/security/SECURITY_SPECIALIST.md
  - workflows/workflow_code_review.md
  - workflows/workflow_developer_tool.md
prerequisites:
  - session_init_done
  - code_review_pass (Architect PASS)
outputs:
  - type: file
    path: "documents/human/reports/security_review_<feature>.md"
  - type: message
    field: "wynik review SECURE / AT_RISK / BLOCKED"
---

# Workflow: Security Review

Po PASS z code review Architekta, Security Specialist analizuje kod pod katem bezpieczenstwa.
Developer poprawia jesli trzeba. Petla review max 2 iteracje.

Pipeline: Developer (implementacja) → Architect (code review PASS) → **Security Specialist (security review)** → next milestone.

## Outline

1. **Zgloszenie do security review** — Architect/Developer przesyla zakres
2. **Security review** — Security Specialist analizuje kod i pisze raport
3. **Decyzja** — SECURE / AT_RISK / BLOCKED
4. **Iteracja** — Developer poprawia (jesli AT_RISK)
5. **Re-review** — Security Specialist weryfikuje poprawki (max 1 re-review)

---

## Faza 1: Zgloszenie do security review

**Owner:** architect (lub developer po PASS architekta)

### Inputs required
- [ ] `code_review_pass`: Architect zakonczyl code review z wynikiem PASS
- [ ] `files_changed`: Lista zmienionych plikow znana

### Steps

## Step 1: Przygotuj opis zakresu security review

**step_id:** prepare_security_request
**action:** Przygotuj opis zakresu: zmienione pliki, cel feature, znane security-relevant aspekty (auth, data flow, external API)
**tool:** Write
**command:** `Write tmp/security_review_request.md`
**verification:** Plik istnieje i zawiera: liste plikow, cel, security-relevant aspekty
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Opis niekompletny. Uzupelnij brakujace sekcje."
**next_step:** send_security_request (if PASS)

---

## Step 2: Wyslij zgloszenie do Security Specialist

**step_id:** send_security_request
**action:** Wyslij opis zakresu do Security Specialist przez agent_bus
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from architect --to security_specialist --content-file tmp/security_review_request.md`
**verification:** Wiadomosc wyslana (brak bledu CLI)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad wysylki. Sprawdz agent_bus_cli."
**next_step:** read_security_request (if PASS)

→ HANDOFF: security_specialist. STOP.
  Mechanizm: agent_bus send
  Czekaj na: raport security review od Security Specialist w inbox.

### Exit Gate

**Checklist:**
- [ ] `scope_described`: Opis zakresu przygotowany (pliki, cel, security aspects)
- [ ] `code_review_pass`: Architect PASS potwierdzone
- [ ] `request_sent`: Wiadomosc wyslana do Security Specialist

**Status:**
- PASS if: wszystkie == true

---

## Faza 2: Security Review

**Owner:** security_specialist

### Inputs required
- [ ] `review_request`: Zgloszenie z opisem zakresu i potwierdzeniem PASS Architekta

### Steps

## Step 3: Przeczytaj zgloszenie i zidentyfikuj zakres

**step_id:** read_security_request
**action:** Przeczytaj zgloszenie, zidentyfikuj zakres plikow, zidentyfikuj trust boundaries i attack surface
**tool:** Read
**command:** `Read` zgloszenia + `Glob` / `Grep` do identyfikacji plikow
**verification:** Lista plikow do review znana, attack surface zidentyfikowane
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Zgloszenie niejasne. Zapytaj Architekta o konkretny zakres."
**next_step:** read_changed_files (if PASS)

---

## Step 4: Przeczytaj zmienione pliki

**step_id:** read_changed_files
**action:** Przeczytaj kazdy zmieniony plik. Zidentyfikuj: input sources, data flows, auth checks, crypto usage, external calls
**tool:** Read
**command:** `Read <sciezka_pliku>` per zmieniony plik
**verification:** Wszystkie zmienione pliki przeczytane
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Plik niedostepny. Sprawdz sciezke."
**next_step:** check_dependencies (if PASS)

---

## Step 5: Sprawdz dependencies

**step_id:** check_dependencies
**action:** Przeczytaj requirements.txt / package.json. Sprawdz znane CVE w dependencies
**tool:** Read, Grep
**command:** `Read requirements.txt` / `Grep "==" requirements.txt`
**verification:** Lista dependencies sprawdzona, znane CVE zidentyfikowane
**on_failure:**
  - retry: yes
  - skip: yes (jesli brak nowych dependencies)
  - escalate: no
  - reason: "Brak pliku dependencies. Sprawdz czy projekt uzywa innego systemu."
**next_step:** check_secrets (if PASS)

---

## Step 6: Sprawdz secrets i konfiguracje

**step_id:** check_secrets
**action:** Grep po plikach: hardcoded secrets, default passwords, API keys. Sprawdz .gitignore, .env handling
**tool:** Grep
**command:** `Grep "password|secret|api_key|token" --type py` + `Grep "hardcoded|changeme|default" --type py`
**verification:** Brak hardcoded secrets lub findings zalogowane
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Secret detection niekompletny. Rozszerz patterny."
**next_step:** evaluate_security (if PASS)

---

## Step 7: Ocen bezpieczenstwo per wymiar

**step_id:** evaluate_security
**action:** Ocen kod per wymiar z security_checklist (SECURITY_SPECIALIST.md): auth, injection, secrets, data, sessions, rate limiting, deps. Dla kazdego finding: scenariusz ataku + severity + mitygacja
**tool:** manual
**command:** Analiza kodu per wymiar. Kazdy finding = scenariusz ataku (nie abstrakcja).
**verification:** Kazdy wymiar oceniony, findings sklasyfikowane (Critical/High/Medium/Low/Info)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Ocena niekompletna. Sprawdz kazdy wymiar z checklist."
**next_step:** write_security_report (if PASS)

---

## Step 8: Napisz raport security review

**step_id:** write_security_report
**action:** Napisz raport security review do pliku w documents/human/reports/
**tool:** Write
**command:** `Write documents/human/reports/security_review_<feature>.md`
**verification:** Plik istnieje, zawiera: Summary (assessment + finding counts), Threat Model, Findings (per severity z attack scenario), OWASP checklist, Recommended Actions
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Raport niekompletny. Uzupelnij brakujace sekcje."
**next_step:** security_assessment (if PASS)

Format raportu — patrz output_contract w SECURITY_SPECIALIST.md.

---

## Decision Point 1: Wynik security review

**decision_id:** security_assessment
**condition:** Brak Critical/High findings
**path_true:** send_secure (SECURE → Faza 3a)
**path_false:** send_at_risk (AT_RISK → Faza 3b) jesli Critical/High obecne
**default:** escalate_blocked (BLOCKED → eskalacja — fundamentalny problem bezpieczenstwa)

### Exit Gate

**Checklist:**
- [ ] `all_files_read`: Wszystkie zmienione pliki przeczytane
- [ ] `checklist_complete`: Security checklist przejrzana per wymiar
- [ ] `report_saved`: Raport zapisany do documents/human/reports/
- [ ] `decision_made`: Decyzja podjeta (SECURE / AT_RISK / BLOCKED)

**Status:**
- PASS if: wszystkie == true

---

## Faza 3a: SECURE

**Owner:** security_specialist

### Steps

## Step 9: Wyslij wynik SECURE do Developera i Architekta

**step_id:** send_secure
**action:** Wyslij SECURE + sciezke do raportu + ewentualne Medium/Low/Info findings
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from security_specialist --to developer --content-file tmp/security_pass.md`
**verification:** Wiadomosc wyslana
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Blad wysylki. Ponow."
**next_step:** END

→ HANDOFF: developer. STOP.
  Mechanizm: agent_bus send
  Developer moze kontynuowac prace. Medium/Low/Info opcjonalne do wdrozenia.

### Exit Gate

**Checklist:**
- [ ] `secure_sent`: Wiadomosc z wynikiem SECURE wyslana

**Status:**
- PASS if: secure_sent == true

---

## Faza 3b: AT_RISK

**Owner:** security_specialist

### Steps

## Step 10: Wyslij wynik AT_RISK do Developera

**step_id:** send_at_risk
**action:** Wyslij AT_RISK z konkretnym feedbackiem: sciezka raportu, Critical/High findings (file:line + attack scenario + fix guidance)
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from security_specialist --to developer --content-file tmp/security_at_risk.md`
**verification:** Wiadomosc wyslana, zawiera Critical/High findings z file:line i scenariuszem ataku
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Blad wysylki. Ponow."
**next_step:** receive_fixes (if PASS)

→ HANDOFF: developer. STOP.
  Mechanizm: agent_bus send
  Czekaj na: Developer poprawia i zglasza re-review.
  Nie poprawiaj kodu sam.

### Exit Gate

**Checklist:**
- [ ] `at_risk_sent`: Raport z feedbackiem wyslany
- [ ] `critical_high_specified`: Critical/High findings wskazane z file:line i attack scenario

**Status:**
- PASS if: wszystkie == true

---

## Faza 3c: BLOCKED (eskalacja)

**Owner:** security_specialist

### Steps

## Step 11: Eskaluj problem bezpieczenstwa

**step_id:** escalate_blocked
**action:** System fundamentalnie niebezpieczny — eskaluj do czlowieka i architekta
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py flag --from security_specialist --reason-file tmp/security_blocked.md`
**verification:** Flag wyslany
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad flagu. Poinformuj czlowieka bezposrednio."
**next_step:** END

### Exit Gate

**Checklist:**
- [ ] `escalated`: Problem wyeskalowany do czlowieka

**Status:**
- PASS if: escalated == true

---

## Faza 4: Re-review (po poprawkach)

**Owner:** security_specialist

### Inputs required
- [ ] `fixes_submitted`: Developer poprawil kod i zglasza ponownie

### Steps

## Step 12: Odbierz poprawki od Developera

**step_id:** receive_fixes
**action:** Odbierz ponowne zgloszenie od Developera z opisem poprawek bezpieczenstwa
**tool:** Read
**command:** Przeczytaj wiadomosc od Developera z inbox
**verification:** Opis poprawek otrzymany
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "Developer nie zglasza poprawek. Czekaj lub eskaluj."
**next_step:** verify_fixes (if PASS)

---

## Step 13: Zweryfikuj poprawki

**step_id:** verify_fixes
**action:** Zweryfikuj TYLKO wskazane Critical/High findings. Nie rozszerzaj zakresu — chyba ze poprawki wprowadzaja nowe luki.
**tool:** Read
**command:** `Read <zmienione_pliki>` — tylko pliki z Critical/High findings
**verification:** Critical/High findings naprawione lub wciaz obecne
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Poprawki niekompletne."
**next_step:** re_review_assessment (if PASS)

---

## Decision Point 2: Wynik re-review

**decision_id:** re_review_assessment
**condition:** Critical/High findings naprawione
**path_true:** send_secure (SECURE — przejdz do Fazy 3a)
**path_false:** escalate_persistent (Critical/High wciaz obecne po 2 iteracjach → BLOCKED)
**default:** escalate_persistent

---

## Step 14: Eskaluj persistentne Critical/High findings

**step_id:** escalate_persistent
**action:** Po 2 iteracjach Critical/High wciaz nie naprawione — eskaluj do czlowieka
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py flag --from security_specialist --reason-file tmp/security_persistent_issues.md`
**verification:** Flag wyslany
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad flagu. Poinformuj czlowieka bezposrednio."
**next_step:** END

### Forbidden

- Wiecej niz 2 iteracje review na ten sam zakres — po 2 iteracjach eskalacja.
- Re-review rozszerza zakres poza oryginalne findings.

### Exit Gate

**Checklist:**
- [ ] `fixes_verified`: Critical/High z pierwszego review zweryfikowane
- [ ] `report_updated`: Raport zaktualizowany lub nowy raport

**Status:**
- PASS if: fixes_verified == true AND Critical/High naprawione
- BLOCKED if: Critical/High wciaz obecne → eskalacja

---

## Wariant: Final Security Audit (przed release)

Trigger: milestone zakonczony, przed deploymentem na produkcje.
Roznica vs security review: pelny scope projektu, nie delta.

### Dodatkowe kroki:
1. Przeczytaj WSZYSTKIE pliki security-relevant (auth, crypto, API, config)
2. Sprawdz git history pod katem leaked secrets: `Grep "password|secret|key" --type py`
3. Sprawdz OWASP Top 10 — kazdy punkt
4. Sprawdz dependency tree — znane CVE
5. Raport koncowy: `documents/human/reports/security_audit_<project>_<version>.md`

Assessment: SECURE / AT_RISK / BLOCKED (te same kryteria)

---

## Forbidden

1. **Security Specialist edytuje kod zamiast pisac raport** — scope leak.
2. **Developer ignoruje Critical/High findings i commituje** — pominiecie gate'u.
3. **Review bez raportu (ustna informacja)** — raport jest artefaktem trwalym.
4. **Review kodu bez przeczytania plikow (ocena po opisie)** — niedopuszczalne.
5. **Finding bez scenariusza ataku** — abstrakcyjne "to niebezpieczne" nie jest finding.

---

## Kiedy eskalacja do czlowieka

- Po 2 iteracjach review Critical/High wciaz nie naprawione
- Fundamentalny problem bezpieczenstwa (architektura nie do naprawienia bez redesign)
- Konflikt Security Specialist ↔ Developer o severity oceny
- Podejrzenie wycieku danych lub incydent bezpieczenstwa

---

## Self-check

- [ ] Wszystkie zmienione pliki przeczytane?
- [ ] Security checklist przejrzana per wymiar?
- [ ] Raport zapisany do documents/human/reports/?
- [ ] Decyzja jednoznaczna (SECURE / AT_RISK / BLOCKED)?
- [ ] Critical/High z file:line i attack scenario (jesli sa)?
- [ ] Wiadomosc do Developera wyslana?
- [ ] Max 2 iteracje review?

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-04-16 | Poczatkowa wersja — security review gate po code review Architekta |

# Handoff Schema — Widok BI

Wspólny kontrakt przekazania między fazami i rolami workflow tworzenia widoku BI.
Każdy handoff musi zawierać wszystkie pola. Brak pola = `BLOCKED`.

---

## Format handoffu

```json
{
  "view_name": "{NazwaWidoku}",
  "from_role": "erp_specialist | analyst",
  "to_role": "analyst | erp_specialist | developer | human",
  "phase_completed": "faza_0 | faza_1a | faza_1b | faza_2 | faza_3 | faza_4",
  "status": "PASS | BLOCKED | ESCALATE",
  "artifacts": [
    "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_draft.sql",
    "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_plan.xlsx",
    "solutions/bi/{NazwaWidoku}/{NazwaWidoku}_export.xlsx"
  ],
  "verification_summary": "Co zostało sprawdzone i jaki wynik.",
  "open_issues": [],
  "missing_items": [],
  "next_expected_action": "Konkretna czynność którą odbierający ma wykonać."
}
```

---

## Reguła handoffu

Przekazanie do kolejnej roli jest dozwolone **wyłącznie przy `status = PASS`**.

Jeśli `status = BLOCKED`:
- Wypełnij `missing_items` — lista braków
- Pozostań w bieżącej fazie
- Nie wysyłaj handoffu do następnej roli

Jeśli `status = ESCALATE`:
- Wyślij flagę do człowieka: `python tools/agent_bus_cli.py flag --from <rola> --reason-file tmp/tmp.md`
- Opisz powód eskalacji i punkt sporny

---

## Przykład PASS (Faza 1a → Analityk)

```json
{
  "view_name": "TraNag",
  "from_role": "erp_specialist",
  "to_role": "analyst",
  "phase_completed": "faza_1a",
  "status": "PASS",
  "artifacts": [
    "solutions/bi/TraNag/TraNag_plan.xlsx"
  ],
  "verification_summary": "Plan zawiera 47 kolumn CDN.TraNag + 5 kolumn z JOINów. Baseline: 12 340 rekordów. Pominięto 3 kolumny (GIDFirma x2, stała techniczna TrN_ArchNum COUNT DISTINCT=1). Enumeracje TrN_GIDTyp (25 typów) zweryfikowane przez CDN.Obiekty.",
  "open_issues": ["Numery dokumentów — czeka na wynik od usera (SELECT z CDN.NazwaObiektu przekazany)"],
  "missing_items": [],
  "next_expected_action": "Analityk recenzuje plan: weryfikacja konwencji + feedback lub zatwierdzenie."
}
```

## Przykład BLOCKED (Faza 2 — brak eksportu)

```json
{
  "view_name": "TraNag",
  "from_role": "erp_specialist",
  "to_role": "analyst",
  "phase_completed": "faza_2",
  "status": "BLOCKED",
  "artifacts": [
    "solutions/bi/TraNag/TraNag_draft.sql"
  ],
  "verification_summary": "",
  "open_issues": [],
  "missing_items": [
    "Brak eksportu TraNag_export.xlsx — sql_query.py nie uruchomiony po ostatniej zmianie.",
    "Self-check: ELSE bez surowej wartości w CASE dla TrN_GIDTyp."
  ],
  "next_expected_action": "ERP Specialist: uruchom sql_query.py --export, popraw CASE, zaktualizuj eksport."
}
```

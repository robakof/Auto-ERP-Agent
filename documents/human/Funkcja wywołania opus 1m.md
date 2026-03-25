
claude-clean --model claude-opus-4-6

 | Element z researchu       | Status w konwencji    | Gap     |
  |---------------------------|-----------------------|---------|
  | Checklist over prose      | ✓ Exit gate checklist | OK      |
  | Explicit phase gate       | ✓ 07R Exit Gate       | OK      |
  | Handoff contract          | ✗ Brak                | BRAKUJE |
  | Structured output (JSON)  | ✗ Brak                | BRAKUJE |
  | State-machine (next_step) | ✓ 04R strict format   | OK      |
  | Inputs required           | ✗ Brak                | BRAKUJE |
  | Required artifacts        | ✗ Brak                | BRAKUJE |
  | Forbidden actions         | ✓ 10R (opcjonalne)    | OK      |
  | Self-check before finish  | ✗ Brak                | BRAKUJE |
  | PASS/BLOCKED/ESCALATE     | ✓ Exit gate           | OK      |







● To wyjaśnia wszystko. Opus 4.5 = 200k max. Tylko Opus 4.6 = 1M.

  Z Twojego wcześniejszego /model output widziałem:
  1. Default (recommended)  Opus 4.5
  2. Sonnet ✔               Sonnet 4.5
  3. Haiku                  Haiku 4.5

  Nie ma tam opcji 4.6 ani [1m]!

  Problem

  Ta instalacja Claude Code nie widzi modeli 4.6. Na nowej maszynie prawdopodobnie były dostępne.

  Co zrobić

  4. Sprawdź czy jest nowsza wersja:
  npm update -g @anthropic-ai/claude-code
  5. Wyczyść cache Claude Code:
  rmdir /s /q "%APPDATA%\claude-code"
  6. (ostrożnie - usunie lokalne ustawienia)
  7. Porównaj z nową maszyną:
    - Co pokazuje tam /model?
    - Jaką wersję Claude Code tam masz?
  8. Wyloguj i zaloguj ponownie:
  claude logout
  claude login

  Jeśli po tych krokach nadal nie widzisz Opus 4.6 / opcji [1m], to problem po stronie konta — skontaktuj się z support@claude.com.


claude logout
  claude login
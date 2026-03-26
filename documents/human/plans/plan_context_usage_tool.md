# Plan: context_usage.py — live token usage tool

## Problem
Agenci piszą "Kontekst: ~XX%" na oko. Dane o zużyciu tokenów są w transkrypcie .jsonl (pisanym live przez Claude Code), ale parsowane dopiero po sesji (on_stop hook). Brak narzędzia do odpytania mid-session.

## Rozwiązanie
`tools/context_usage.py` — parsuje live transcript, sumuje token_usage, zwraca JSON z % kontekstu.

## Wywołania
```
py tools/context_usage.py                    # bieżąca sesja (najnowszy transcript)
py tools/context_usage.py --transcript PATH  # konkretny plik
py tools/context_usage.py --session-id UUID  # lookup z live_agents.transcript_path
```

## Autodetekcja bieżącej sesji
1. Najnowszy .jsonl w `~/.claude/projects/<project-key>/` (posortowany po mtime)
2. Filtr: pomijaj pliki < 100 bytes (puste/fragmentaryczne)

## Output JSON
```json
{
  "ok": true,
  "transcript": "path/to/file.jsonl",
  "turns": 42,
  "input_tokens": 150000,
  "output_tokens": 25000,
  "cache_read_tokens": 100000,
  "cache_create_tokens": 5000,
  "total_tokens": 280000,
  "context_window": 1000000,
  "context_used_pct": 28.0
}
```

## Reuse
- `jsonl_parser.parse_jsonl()` — parsowanie (już testowane)
- `read_transcript.py` — wzorzec TRANSCRIPTS_DIR

## Testy
- test z fixture .jsonl (3-4 turny, znane token counts)
- test autodetect (mock mtime)
- test --transcript z plikiem

## Effort: mała (reuse istniejących komponentów)

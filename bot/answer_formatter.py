"""
AnswerFormatter — Claude API call 2: dane SQL → odpowiedź w języku polskim.

Obsługuje:
- brak wyników (bez wywołania API)
- błąd SQL (bez wywołania API)
- normalne wyniki → Claude formatuje odpowiedź
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import anthropic
from dotenv import load_dotenv

from bot.sql_executor import ExecutionResult

load_dotenv()

DEFAULT_MODEL = os.getenv("BOT_MODEL_FORMAT", "claude-haiku-4-5-20251001")
MAX_TOKENS = 500

SYSTEM_PROMPT = """Jesteś asystentem danych dla firmy. Otrzymujesz pytanie użytkownika oraz wyniki zapytania SQL z systemu ERP.
Twoim zadaniem jest sformułowanie zwięzłej, rzeczowej odpowiedzi po polsku na podstawie danych.

Zasady formatowania:
- Używaj WYŁĄCZNIE formatowania HTML: <b>pogrubienie</b>, <i>kursywa</i>
- NIE używaj markdown: żadnych #, *, **, _, ~~~
- Tabele przedstawiaj jako zwykły tekst z wyrównaniem spacjami lub jako listę
- Liczby kluczowe ujmuj w <b></b>

Zasady merytoryczne:
- Odpowiadaj po polsku, konkretnie i zwięźle
- Gdy pytanie dotyczy okresu (np. "1-10 marca") — skup się na tym okresie i porównaj z tym samym okresem rok wcześniej
- Pokazuj różnicę (wzrost/spadek) między latami, nie sumę historyczną
- Jeśli dane zawierają ranking — pokaż tylko top pozycje z liczbami, bez zbędnego komentarza
- Nie wymyślaj danych których nie ma w wynikach
- Nie wyjaśniaj jak działasz"""


class AnswerFormatter:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

    def format(self, question: str, execution_result: ExecutionResult, history: str) -> str:
        if not execution_result.ok:
            return "Wystąpił błąd podczas wykonywania zapytania. Spróbuj przeformułować pytanie."

        if execution_result.row_count == 0:
            return "Nie znaleziono danych spełniających kryteria pytania."

        user_content = self._build_user_message(question, execution_result, history)

        message = self._client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        return message.content[0].text

    def _build_user_message(self, question: str, result: ExecutionResult, history: str) -> str:
        parts = []

        if history:
            parts.append(f"Historia rozmowy:\n{history}\n")

        parts.append(f"Pytanie: {question}")

        headers = " | ".join(result.columns)
        rows_text = "\n".join(" | ".join(str(v) for v in row) for row in result.rows)
        parts.append(f"\nWyniki ({result.row_count} wierszy):\n{headers}\n{rows_text}")

        return "\n".join(parts)

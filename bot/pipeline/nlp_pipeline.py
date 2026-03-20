"""
NlpPipeline — orkiestrator pipeline bota.

Przepływ:
  pytanie
    → historia konwersacji
    → Claude API call 1: generowanie SQL
    → SqlValidator: walidacja
    → SqlExecutor: wykonanie
    → AnswerFormatter: Claude API call 2
    → zapis tury + logowanie
    → odpowiedź
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import anthropic
from dotenv import load_dotenv

from bot.answer_formatter import AnswerFormatter
from bot.pipeline.conversation import ConversationManager
from bot.pipeline.sql_validator import SqlValidator
from bot.sql_executor import SqlExecutor

load_dotenv()

DEFAULT_MODEL = os.getenv("BOT_MODEL_GENERATE", "claude-sonnet-4-6")
CATALOG_PATH = Path(__file__).parent.parent.parent / "solutions" / "bi" / "catalog.json"
BUSINESS_CONTEXT_PATH = Path(__file__).parent.parent / "config" / "business_context.txt"
DEFAULT_LOG_DIR = Path(__file__).parent.parent.parent / "logs" / "bot"

NO_SQL_MARKER = "NO_SQL"

SYSTEM_PROMPT_TEMPLATE = """Jesteś asystentem danych dla firmy. Twoim zadaniem jest generowanie zapytań SQL na podstawie pytań użytkownika.

{business_context}

Dostępne widoki w schemacie AIBI:
{catalog}

Zasady:
- Generuj WYŁĄCZNIE zapytania SELECT na schemacie AIBI.*
- Nie używaj innych schematów (CDN.*, dbo.* itp.)
- Zawsze dodaj TOP N (max 200) jeśli pytanie nie wymaga pełnych danych
- Jeśli pytanie jest częściowo poza zakresem — wygeneruj SQL dla dostępnej części (pomiń niedostępne dane)
- NO_SQL tylko gdy pytanie jest CAŁKOWICIE poza zakresem (np. pogoda, kadrowe, tematy niezwiązane z ERP)
- Unikaj HAVING z dzieleniem i złożonymi wyrażeniami — zamiast tego używaj prostego GROUP BY + ORDER BY
- Do porównań rok-do-roku używaj SUM(CASE WHEN YEAR(...)=X THEN 1 ELSE 0 END) w SELECT, bez HAVING
- Zwróć TYLKO czysty SQL bez markdown, bez wyjaśnień, bez komentarzy"""


@dataclass
class PipelineResult:
    answer: str
    sql: str | None
    row_count: int
    error: str | None


class NlpPipeline:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        self.model = DEFAULT_MODEL
        self.conversation = ConversationManager()
        self.validator = SqlValidator()
        self.executor = SqlExecutor()
        self.formatter = AnswerFormatter()
        self.log_dir = DEFAULT_LOG_DIR
        self._catalog_text = self._load_catalog()
        self._business_context = self._load_business_context()

    def _load_business_context(self) -> str:
        if not BUSINESS_CONTEXT_PATH.exists():
            return ""
        return BUSINESS_CONTEXT_PATH.read_text(encoding="utf-8")

    def _load_catalog(self) -> str:
        if not CATALOG_PATH.exists():
            return "(brak katalogu widoków)"
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        lines = []
        for view in catalog.get("views", []):
            lines.append(f"Widok: {view['name']}")
            lines.append(f"  Opis: {view['description']}")
            lines.append(f"  Kolumny: {', '.join(view['columns'])}")
            lines.append(f"  Przykładowe pytania: {'; '.join(view['example_questions'])}")
        return "\n".join(lines)

    def run(self, user_id: str, question: str) -> PipelineResult:
        start = time.monotonic()
        history = self.conversation.format_history(user_id)

        # Call 1: generowanie SQL
        sql = self._generate_sql(question, history)

        if sql.strip() == NO_SQL_MARKER:
            answer = "To pytanie wykracza poza zakres danych dostępnych w systemie."
            self.conversation.save_turn(user_id, question, answer)
            self._log(user_id, question, None, 0, answer, time.monotonic() - start)
            return PipelineResult(answer=answer, sql=None, row_count=0, error="OUT_OF_SCOPE")

        # Walidacja
        validation = self.validator.validate(sql)
        if not validation.ok:
            answer = "Nie udało się wygenerować poprawnego zapytania. Spróbuj przeformułować pytanie."
            self._log(user_id, question, sql, 0, answer, time.monotonic() - start)
            return PipelineResult(answer=answer, sql=sql, row_count=0, error="VALIDATION_ERROR")

        # Wykonanie
        execution = self.executor.execute(validation.sql)

        # Call 2: formatowanie odpowiedzi
        answer = self.formatter.format(
            question=question,
            execution_result=execution,
            history=history,
        )

        self.conversation.save_turn(user_id, question, answer)
        self._log(user_id, question, validation.sql, execution.row_count, answer, time.monotonic() - start)

        return PipelineResult(
            answer=answer,
            sql=validation.sql,
            row_count=execution.row_count,
            error=None,
        )

    def _generate_sql(self, question: str, history: str) -> str:
        system = SYSTEM_PROMPT_TEMPLATE.format(catalog=self._catalog_text, business_context=self._business_context)
        user_content = question
        if history:
            user_content = f"Historia rozmowy:\n{history}\n\nPytanie: {question}"

        message = self._client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=system,
            messages=[{"role": "user", "content": user_content}],
        )
        return self._strip_markdown(message.content[0].text.strip())

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Usuwa owijanie ```sql ... ``` które niektóre modele dodają mimo instrukcji."""
        if text.startswith("```"):
            lines = text.splitlines()
            # usuń pierwszą linię (```sql lub ```) i ostatnią (```)
            inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            return "\n".join(inner).strip()
        return text

    def _log(self, user_id: str, question: str, sql: str | None, row_count: int, answer: str, duration_s: float) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        entry = {
            "ts": datetime.now().isoformat(),
            "user_id": user_id,
            "question": question,
            "generated_sql": sql,
            "row_count": row_count,
            "answer": answer,
            "duration_ms": round(duration_s * 1000),
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bot pipeline CLI")
    parser.add_argument("--question", required=True, help="Pytanie do bota")
    parser.add_argument("--verbose", action="store_true", help="Pokaż wygenerowany SQL")
    args = parser.parse_args()

    pipeline = NlpPipeline()
    result = pipeline.run(user_id="cli", question=args.question)

    if args.verbose and result.sql:
        print(f"\n[SQL]\n{result.sql}\n")
    print(f"\n[Odpowiedź]\n{result.answer}")
    if result.error:
        print(f"\n[Status] {result.error}")

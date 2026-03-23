"""
photo_preprocess.py — Wsadowe skalowanie proporcjonalne zdjęć katalogowych.

Przepływ:
    1. Zbiera pliki PNG z katalogu wejściowego.
    2. Pobiera wysokości produktów z ERP (CDN.Atrybuty, AtkId=12).
    3. Wyznacza MAX_HEIGHT_CM = max z pobranych wysokości (skala wspólna dla wsadu).
    4. Skaluje każde zdjęcie proporcjonalnie i wkleja na canvas 1000×1000.
    5. Zapisuje do katalogu wyjściowego pod tą samą nazwą pliku.

CLI:
    python tools/photo_preprocess.py --input-dir PATH --output-dir PATH

Wzór skalowania (PROMPT_PHOTO_PROCESSING.md):
    canvas   = 1000 × 1000 px
    AREA_H   = 800 px  (y=100..900)
    BASE_Y   = 900 px  (wspólna podstawa)
    target_h = round((height_cm / max_height_cm) * AREA_H)
"""

import argparse
import sys
from pathlib import Path
from typing import Callable, Optional

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.output import print_json
from tools.lib.sql_client import SqlClient

_PROJECT_ROOT = Path(__file__).parent.parent
SQL_PATH = _PROJECT_ROOT / "solutions/catalog/photo_heights.sql"

CANVAS_PX   = 1000
AREA_H_PX   = 800
BASE_Y_PX   = 900


# ---------------------------------------------------------------------------
# ERP
# ---------------------------------------------------------------------------

def load_heights(kody: list[str]) -> dict[str, float]:
    """Pobiera wysokości produktów z ERP. Zwraca {kod: height_cm}."""
    if not kody:
        return {}
    sql_template = SQL_PATH.read_text(encoding="utf-8")
    placeholders = ", ".join(f"'{k}'" for k in kody)
    sql = sql_template.replace("{placeholders}", placeholders)
    result = SqlClient().execute(sql, inject_top=None)
    if not result["ok"]:
        raise RuntimeError(result["error"]["message"])
    return {row[0]: float(row[1]) for row in result["rows"]}


# ---------------------------------------------------------------------------
# Skalowanie
# ---------------------------------------------------------------------------

def _scale_params(height_cm: float, max_height_cm: float, orig_w: int, orig_h: int) -> tuple:
    """Zwraca (target_w, target_h, x, y) dla canvas 1000×1000."""
    target_h = round((height_cm / max_height_cm) * AREA_H_PX)
    target_w = round(target_h * (orig_w / orig_h))
    x = (CANVAS_PX - target_w) // 2
    y = BASE_Y_PX - target_h
    return target_w, target_h, x, y


def process_image(input_path: Path, output_path: Path, height_cm: float, max_height_cm: float) -> None:
    """Skaluje zdjęcie proporcjonalnie i zapisuje na canvas 1000×1000 (białe tło)."""
    img = Image.open(input_path).convert("RGBA")
    target_w, target_h, x, y = _scale_params(height_cm, max_height_cm, img.width, img.height)
    resized = img.resize((target_w, target_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS_PX, CANVAS_PX), (255, 255, 255, 255))
    canvas.paste(resized, (x, y), resized)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(str(output_path), "PNG")


# ---------------------------------------------------------------------------
# Wsad
# ---------------------------------------------------------------------------

def batch_process(
    input_dir: Path,
    output_dir: Path,
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
) -> dict:
    """
    Przetwarza wszystkie PNG z input_dir do output_dir.

    progress_cb(current, total, filename) — opcjonalny callback postępu.
    Zwraca {"ok": True, "processed": N, "skipped": [...], "errors": [...]}.
    """
    files = sorted({f for f in input_dir.iterdir()
                    if f.suffix.lower() == ".png" and f.is_file()})
    if not files:
        return {"ok": True, "processed": 0, "skipped": [], "errors": []}

    kody = [f.stem for f in files]
    heights = load_heights(kody)

    skipped = [k for k in kody if k not in heights]
    to_process = [(f, heights[f.stem]) for f in files if f.stem in heights]

    if not to_process:
        return {"ok": True, "processed": 0, "skipped": skipped, "errors": []}

    max_height_cm = max(h for _, h in to_process)
    errors = []

    for i, (f, height_cm) in enumerate(to_process):
        if progress_cb:
            progress_cb(i + 1, len(to_process), f.name)
        try:
            process_image(f, output_dir / f.name, height_cm, max_height_cm)
        except Exception as e:
            errors.append({"file": f.name, "error": str(e)})

    return {
        "ok": True,
        "processed": len(to_process) - len(errors),
        "skipped": skipped,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Wsadowe skalowanie zdjęć katalogowych.")
    parser.add_argument("--input-dir",  required=True, help="Katalog ze zdjęciami PNG po GPT-4o")
    parser.add_argument("--output-dir", required=True, help="Katalog wyjściowy dla przetworzonych zdjęć")
    args = parser.parse_args()

    result = batch_process(Path(args.input_dir), Path(args.output_dir))
    print_json({"ok": result["ok"], "data": result, "error": None, "meta": {}})


if __name__ == "__main__":
    main()

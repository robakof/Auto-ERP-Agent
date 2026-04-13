"""Smoke test dla raport_kasowy_to_txt — konwersja wzorcowego pliku xlsx."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
TOOL = ROOT / "tools" / "raport_kasowy_to_txt.py"
INPUT = ROOT / "documents" / "Wzory plików" / "Raport kasowy.xlsx"


def test_konwersja_xlsx_do_txt(tmp_path):
    output = tmp_path / "raport.txt"

    result = subprocess.run(
        [sys.executable, str(TOOL), "--input", str(INPUT), "--output", str(output)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    assert output.exists()

    text = output.read_bytes().decode("cp1250")
    lines = [l for l in text.split("\r\n") if l.strip()]

    # 801 transakcji w wzorcowym xlsx (788 PA + 13 KW)
    assert len(lines) == 801, f"Expected 801 lines, got {len(lines)}"

    # Kazda linia: 15 pol = 14 przecinkow (wewnatrz cudzyslowow brak)
    # Sprawdzimy pierwsza i ostatnia linie
    for line in (lines[0], lines[-1]):
        # Wzorzec: 0,"data","czas",typ,"akronim","prefix",numer,"sufix","tresc","","POSS",kwota,0,0,0
        parts_outside_quotes = line.split('"')
        # Po splicie po cudzyslowach - liczba elementow nieparzysta
        assert len(parts_outside_quotes) >= 15

    # Pierwsza linia: znana z wzorcowego xlsx (R3)
    expected_first = '0,"26/03/11","12:35:05",1,"JEDNORAZOWY","PA-",1441,"/03/26/CME","POS_SZAMOTULY1, PA-1441/03/26/CME","","POSS",8,0,0,0'
    assert lines[0] == expected_first, f"\nExpected: {expected_first}\nGot:      {lines[0]}"

    # KW musi miec typ=2
    kw_lines = [l for l in lines if ',"KW/",' in l]
    assert len(kw_lines) == 13, f"Expected 13 KW lines, got {len(kw_lines)}"
    for kw in kw_lines:
        assert kw.split(",")[3] == "2", f"KW line should have typ=2: {kw}"

    # PA musi miec typ=1
    pa_lines = [l for l in lines if ',"PA-",' in l]
    assert len(pa_lines) == 788, f"Expected 788 PA lines, got {len(pa_lines)}"
    for pa in pa_lines:
        assert pa.split(",")[3] == "1", f"PA line should have typ=1: {pa}"

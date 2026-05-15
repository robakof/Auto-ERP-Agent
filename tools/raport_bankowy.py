"""
raport_bankowy.py — parser wyciągów MT940 (.eMT) → CSV.

Wczytuje pliki MT940 z podanego katalogu (lub pojedynczy plik),
parsuje transakcje i zapisuje zbiorczy CSV.

CLI:
    py tools/raport_bankowy.py --input <katalog_lub_plik> --output <wynik.csv>
"""

import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path


# :61: line format: YYMMDD[CD]amount,decFtypeNONREF
RE_61 = re.compile(
    r"^:61:(\d{6})"         # data YYMMDD
    r"([CD])"               # C=credit, D=debit
    r"N?"                   # opcjonalne N
    r"(\d+,\d+)"            # kwota z przecinkiem
    r"([A-Z]{4})"           # typ operacji (NTRF, FCHG, ...)
    r"(.*)$"                # reszta (NONREF itp.)
)

# :60F: / :62F: saldo: C/D + YYMMDD + waluta + kwota
RE_SALDO = re.compile(
    r"^:(\d{2}F):([CD])(\d{6})([A-Z]{3})(\d+,\d+)$"
)

# :86: subpola ?XX
RE_SUBFIELD = re.compile(r"\?(\d{2})")

CSV_COLUMNS = [
    "data", "typ", "kwota", "waluta",
    "saldo_otwarcia", "saldo_zamkniecia",
    "nr_rachunku_kontrahenta", "kontrahent",
    "tytul", "kod_operacji", "nr_wyciagu", "plik",
]


def _parse_amount(raw: str) -> str:
    """'77647,67' → '77647.67'."""
    return raw.replace(",", ".")


def _parse_date(raw: str) -> str:
    """'260401' → '2026-04-01'."""
    dt = datetime.strptime(raw, "%y%m%d")
    return dt.strftime("%Y-%m-%d")


def _parse_86(raw: str) -> dict:
    """Parsuje pole :86: z subpolami ?XX.

    Zwraca dict: kod_operacji, tytul, nr_rachunku, kontrahent.
    """
    result = {"kod_operacji": "", "tytul": "", "nr_rachunku": "", "kontrahent": ""}

    # Rozbij na subpola
    parts = RE_SUBFIELD.split(raw)
    # parts[0] = kod operacji (przed pierwszym ?XX)
    # potem pary: [kod, wartość, kod, wartość, ...]
    if parts:
        result["kod_operacji"] = parts[0].strip()

    subfields = {}
    i = 1
    while i < len(parts) - 1:
        subfields[parts[i]] = parts[i + 1]
        i += 2

    result["tytul"] = subfields.get("20", "").strip()
    result["nr_rachunku"] = subfields.get("31", "").strip()
    result["kontrahent"] = subfields.get("32", "").strip()

    return result


def parse_mt940(filepath: Path) -> list[dict]:
    """Parsuje plik MT940, zwraca listę transakcji."""
    text = filepath.read_text(encoding="cp1250", errors="replace")
    lines = text.splitlines()

    transactions = []
    nr_wyciagu = ""
    waluta = "PLN"
    saldo_otwarcia = ""
    saldo_zamkniecia = ""
    filename = filepath.name

    # Zbierz wieloliniowe pola — MT940 łamie :86: na wiele linii
    merged = []
    for line in lines:
        if line.startswith(":") or line.startswith("{") or line.startswith("-}"):
            merged.append(line)
        elif merged:
            merged[-1] += line

    # Pass 1: nagłówki
    for line in merged:
        m_saldo = RE_SALDO.match(line)
        if m_saldo:
            tag = m_saldo.group(1)
            kwota = _parse_amount(m_saldo.group(5))
            waluta = m_saldo.group(4)
            if tag == "60F":
                saldo_otwarcia = kwota
            elif tag == "62F":
                saldo_zamkniecia = kwota
        elif line.startswith(":28C:"):
            nr_wyciagu = line[5:].strip()

    # Pass 2: transakcje (:61: + :86:)
    i = 0
    while i < len(merged):
        line = merged[i]
        m61 = RE_61.match(line)
        if m61:
            data = _parse_date(m61.group(1))
            typ = m61.group(2)
            kwota = _parse_amount(m61.group(3))
            typ_op = m61.group(4)

            # Szukaj :86: zaraz po :61:
            info = {"kod_operacji": "", "tytul": "", "nr_rachunku": "", "kontrahent": ""}
            if i + 1 < len(merged) and merged[i + 1].startswith(":86:"):
                raw86 = merged[i + 1][4:]  # skip ":86:"
                info = _parse_86(raw86)
                i += 1

            transactions.append({
                "data": data,
                "typ": typ,
                "kwota": kwota,
                "waluta": waluta,
                "saldo_otwarcia": saldo_otwarcia,
                "saldo_zamkniecia": saldo_zamkniecia,
                "nr_rachunku_kontrahenta": info["nr_rachunku"],
                "kontrahent": info["kontrahent"],
                "tytul": info["tytul"],
                "kod_operacji": info["kod_operacji"],
                "nr_wyciagu": nr_wyciagu,
                "plik": filename,
            })
        i += 1

    return transactions


def convert(input_path: Path, output_path: Path) -> dict:
    """Parsuje MT940 z katalogu lub pliku, zapisuje CSV. Zwraca statystyki."""
    if input_path.is_dir():
        files = sorted(input_path.glob("*.eMT"))
        if not files:
            print(f"Brak plików .eMT w {input_path}")
            sys.exit(1)
    else:
        files = [input_path]

    all_transactions = []
    for f in files:
        txns = parse_mt940(f)
        all_transactions.extend(txns)
        print(f"  {f.name}: {len(txns)} transakcji")

    # Sortuj po dacie
    all_transactions.sort(key=lambda t: t["data"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, delimiter=";")
        writer.writeheader()
        writer.writerows(all_transactions)

    return {"files": len(files), "transactions": len(all_transactions)}


def main():
    parser = argparse.ArgumentParser(description="Wyciągi MT940 (.eMT) → CSV.")
    parser.add_argument("--input", required=True,
                        help="Katalog z plikami .eMT lub pojedynczy plik")
    parser.add_argument("--output", required=True, help="Ścieżka wynikowego CSV")
    args = parser.parse_args()

    stats = convert(Path(args.input), Path(args.output))
    print(f"\nOK: {stats['transactions']} transakcji z {stats['files']} plikow -> {args.output}")


if __name__ == "__main__":
    main()

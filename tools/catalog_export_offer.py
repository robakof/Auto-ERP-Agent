"""Export 2026 BRICO DDD products from ERP using offer Excel as product list."""
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import openpyxl
from dotenv import load_dotenv
import pyodbc

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

# --- 1. Read product codes from offer Excel ---
OFFER = Path("C:/Users/arkadiusz/Desktop/Katalog 2026/2 etap/ofertowanie_2026___BRICO_DDD_2026-05-06_gotowy (2).xlsx")
wb = openpyxl.load_workbook(str(OFFER), read_only=True, data_only=True)
ws = wb.active
offer_codes = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0]:
        offer_codes.append(str(row[0]).strip())
wb.close()
print(f"Offer codes: {len(offer_codes)}")

# --- 2. Query ERP for these products ---
conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.getenv('SQL_SERVER')};"
    f"DATABASE={os.getenv('SQL_DATABASE')};"
    f"UID={os.getenv('SQL_USERNAME')};"
    f"PWD={os.getenv('SQL_PASSWORD')};"
    "TrustServerCertificate=yes;"
)
conn = pyodbc.connect(conn_str, timeout=30)
cur = conn.cursor()

products = []
# Batch query (500 at a time)
for i in range(0, len(offer_codes), 500):
    batch = offer_codes[i:i+500]
    ph = ",".join(["?"] * len(batch))
    cur.execute(f"""
        SELECT KodXL, KodEAN, NazwaHandlowa, GrupaSciezka,
               CenaNetto, CennikRodzaj,
               CzasPalenia_h, GramaturaWkladu_g,
               WysokoscNetto_cm, SzerokoscNetto_cm,
               SrednicaProduktu_cm, Material, Zapach,
               WagaProduktu_g, SrednicaOtworu_cm,
               SzerokoscBrutto_cm, WysokoscBrutto_cm, GlebokoscBrutto_cm,
               SztWOpakowaniu, SztNaWarstwie, SztNaPalecie,
               Sezon, Kolor, MaZdjecie, TwrGIDNumer
        FROM AIOP.vKatalogProdukty
        WHERE KodXL IN ({ph})
    """, batch)
    cols = [c[0] for c in cur.description]
    for row in cur.fetchall():
        d = {}
        for j, v in enumerate(row):
            d[cols[j]] = float(v) if isinstance(v, Decimal) else v
        products.append(d)

print(f"Raw rows from ERP: {len(products)}")

# Dedup: one row per KodXL (highest CenaNetto)
best = {}
for p in products:
    code = p["KodXL"]
    price = p.get("CenaNetto") or 0
    if code not in best or price > (best[code].get("CenaNetto") or 0):
        best[code] = p
products = list(best.values())

# Override GrupaSciezka for all
for p in products:
    p["GrupaSciezka"] = "OFERTY/2026/BRICO DDD"

# Check missing
found_codes = set(p["KodXL"] for p in products)
missing = [c for c in offer_codes if c not in found_codes]
print(f"Products from ERP: {len(products)}")
print(f"Missing in ERP: {len(missing)}")
if missing:
    for m in missing[:20]:
        print(f"  {m}")

# --- 3. Packages ---
cur.execute("""
    SELECT PakietKod, PakietNazwa, ProduktKod, ProduktNazwa, IloscSzt
    FROM AIOP.vKatalogPakiety ORDER BY PakietKod, ProduktKod
""")
pkgs = {}
for row in cur.fetchall():
    kod = row[0]
    if kod not in pkgs:
        pkgs[kod] = {"pakiet_kod": kod, "pakiet_nazwa": row[1], "skladniki": []}
    pkgs[kod]["skladniki"].append({
        "kod": row[2], "nazwa": row[3], "ilosc_szt": int(row[4]) if row[4] else 0,
    })
packages = list(pkgs.values())
print(f"Packages: {len(packages)}")

conn.close()

# --- 4. Save ---
OUT = Path("C:/Users/arkadiusz/Desktop/Katalog 2026/2 etap/data")
(OUT / "catalog_products.json").write_text(
    json.dumps({"count": len(products), "products": products},
               ensure_ascii=False, indent=2, default=str),
    encoding="utf-8")
(OUT / "catalog_packages.json").write_text(
    json.dumps({"count": len(packages), "packages": packages},
               ensure_ascii=False, indent=2, default=str),
    encoding="utf-8")
print(f"Saved to {OUT}")

# Price stats
with_price = sum(1 for p in products if (p.get("CenaNetto") or 0) > 0)
print(f"With price > 0: {with_price}/{len(products)}")

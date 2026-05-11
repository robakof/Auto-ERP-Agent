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
          AND CennikNazwa = 'Cennik Brico DDD'
    """, batch)
    cols = [c[0] for c in cur.description]
    for row in cur.fetchall():
        d = {}
        for j, v in enumerate(row):
            d[cols[j]] = float(v) if isinstance(v, Decimal) else v
        products.append(d)

print(f"Raw rows from ERP: {len(products)}")

# Dedup: one row per KodXL (cennik Brico DDD already filtered)
best = {}
for p in products:
    code = p["KodXL"]
    if code not in best:
        best[code] = p

# Fallback: products missing from "Cennik Brico DDD" — try "katalog 2025 Brico"
missing_codes = [c for c in offer_codes if c not in best]
if missing_codes:
    print(f"Fallback query for {len(missing_codes)} missing products...")
    for i in range(0, len(missing_codes), 500):
        batch = missing_codes[i:i+500]
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
              AND CennikNazwa = 'katalog 2025 Brico'
        """, batch)
        cols = [c[0] for c in cur.description]
        for row in cur.fetchall():
            d = {}
            for j, v in enumerate(row):
                d[cols[j]] = float(v) if isinstance(v, Decimal) else v
            code = d["KodXL"]
            if code not in best:
                best[code] = d

products = list(best.values())

# --- 2b. Default group from ERP tree (for standalone product grouping) ---
# Find the sub-category group for each product by walking up from assigned groups.
# Tree: 01_CMENTARZ(1) → 1_ZNICZE(10) → 1_MINI(60), 2_MAŁE, 3_ŚREDNIE, 8_SOLARNE...
#                       → 2_WKŁADY(11) → 6_LEDOWE(49), ...
#                       → 3_LAMPIONY(185)
# We want the group whose parent is a child of 01_CMENTARZ (parent in {10,11,185,12,19})
# i.e., the "leaf category" like 8_SOLARNE, 1_MINI, 6_LEDOWE
gid_to_code = {p["TwrGIDNumer"]: p["KodXL"] for p in products}
gids = list(gid_to_code.keys())
group_map = {}  # KodXL -> GrupaDomyslna

# Known sub-category parents (children of 01_CMENTARZ id=1):
# 1_ZNICZE=10, 2_WKŁADY=11, 3_LAMPIONY=185, 4_DEKORACJE=12, 5_ZNICZOMATY=19
# And for DOM: children of 02_DOM id=2
SUB_CAT_PARENTS = {10, 11, 185, 12, 19}
# Also include direct children of 01_CMENTARZ (id=1) and 02_DOM (id=2)
MAIN_CAT_IDS = {1, 2}

for i in range(0, len(gids), 500):
    batch = gids[i:i+500]
    ph = ",".join(["?"] * len(batch))
    # Get assigned group + its parent + grandparent
    cur.execute(f"""
        SELECT d.TGD_GIDNumer, g.TwG_Kod, g.TwG_GrONumer,
               pg.TwG_Kod AS ParentKod, pg.TwG_GrONumer AS GrandparentId
        FROM CDN.TwrGrupyDom d
        JOIN CDN.TwrGrupy g ON d.TGD_GrONumer = g.TwG_GIDNumer
        LEFT JOIN CDN.TwrGrupy pg ON g.TwG_GrONumer = pg.TwG_GIDNumer
        WHERE d.TGD_GIDNumer IN ({ph})
    """, batch)
    for row in cur.fetchall():
        gid_num = row[0]
        grp_kod = row[1]
        grp_parent = row[2]
        parent_kod = row[3]
        grandparent_id = row[4]
        if gid_num not in gid_to_code:
            continue
        code = gid_to_code[gid_num]
        if code in group_map:
            continue
        # Case 1: group is directly under a known sub-category (e.g. 1_MINI under 1_ZNICZE)
        if grp_parent in SUB_CAT_PARENTS:
            group_map[code] = grp_kod
        # Case 2: group IS a sub-category itself (e.g. 3_LAMPIONY under 01_CMENTARZ)
        elif grp_parent in MAIN_CAT_IDS:
            group_map[code] = grp_kod

for p in products:
    p["GrupaDomyslna"] = group_map.get(p["KodXL"])

grp_stats = {}
for p in products:
    g = p.get("GrupaDomyslna") or "(brak)"
    grp_stats[g] = grp_stats.get(g, 0) + 1
print("Default groups:")
for g in sorted(grp_stats, key=lambda x: grp_stats[x], reverse=True):
    print(f"  {g}: {grp_stats[g]}")

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

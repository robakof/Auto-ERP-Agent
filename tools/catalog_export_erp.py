"""Export catalog products from ERP by offer folder + price list.

Usage:
    py tools/catalog_export_erp.py --folder "OFERTY/2026/BRICO DDD" --pricelist "Cennik Brico DDD"
    py tools/catalog_export_erp.py --folder "OFERTY/2026/BRICO DDD" --pricelist "Cennik Brico DDD" --fallback "katalog 2025 Brico"
    py tools/catalog_export_erp.py --folder "OFERTY/2026/AUCHAN" --pricelist "Cennik Auchan 2026"
    py tools/catalog_export_erp.py --config config/catalogs/ceim_brico_2026.yaml
"""
import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")


def _connect():
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('SQL_SERVER')};"
        f"DATABASE={os.getenv('SQL_DATABASE')};"
        f"UID={os.getenv('SQL_USERNAME')};"
        f"PWD={os.getenv('SQL_PASSWORD')};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=30)


def _row_to_dict(cols, row):
    d = {}
    for j, v in enumerate(row):
        d[cols[j]] = float(v) if isinstance(v, Decimal) else v
    return d


PRODUCT_COLUMNS = """KodXL, KodEAN, NazwaHandlowa, GrupaSciezka,
       CenaNetto, CennikRodzaj, CennikNazwa,
       CzasPalenia_h, GramaturaWkladu_g,
       WysokoscNetto_cm, SzerokoscNetto_cm,
       SrednicaProduktu_cm, Material, Zapach,
       WagaProduktu_g, SrednicaOtworu_cm,
       SzerokoscBrutto_cm, WysokoscBrutto_cm, GlebokoscBrutto_cm,
       SztWOpakowaniu, SztNaWarstwie, SztNaPalecie,
       Sezon, Kolor, MaZdjecie, TwrGIDNumer"""


# --- 1. Find products by offer folder ---

def find_products_by_folder(cur, folder_path: str) -> list[str]:
    """Find product codes assigned to a folder in TwrGrupyDom tree.

    folder_path: e.g. "OFERTY/2026/BRICO DDD"
    Maps to TwrGrupy tree: 10_OFERTY -> 2026 -> BRICO DDD
    """
    parts = folder_path.strip("/").split("/")
    # First part: add "10_" prefix convention for OFERTY
    root_kod = f"10_{parts[0]}" if parts[0].upper() == "OFERTY" else parts[0]

    # Find the target folder by walking down the tree
    cur.execute(
        "SELECT TwG_GIDNumer FROM CDN.TwrGrupy WHERE TwG_Kod = ?", root_kod
    )
    row = cur.fetchone()
    if not row:
        print(f"ERROR: Root folder '{root_kod}' not found in TwrGrupy")
        return []
    parent_id = row[0]

    for part in parts[1:]:
        cur.execute("""
            SELECT TwG_GIDNumer FROM CDN.TwrGrupy
            WHERE TwG_GrONumer = ? AND TwG_Kod = ?
        """, parent_id, part)
        row = cur.fetchone()
        if not row:
            print(f"ERROR: Subfolder '{part}' not found under parent {parent_id}")
            return []
        parent_id = row[0]

    target_folder_id = parent_id
    print(f"Folder '{folder_path}' -> TwG_GIDNumer = {target_folder_id}")

    # In Comarch XL, products in an offer folder are sub-groups (children),
    # where each sub-group TwG_Kod = product Twr_Kod
    cur.execute("""
        SELECT g.TwG_Kod
        FROM CDN.TwrGrupy g
        WHERE g.TwG_GrONumer = ?
    """, target_folder_id)
    subfolder_codes = [r[0] for r in cur.fetchall()]

    # Verify these codes exist as products
    codes = []
    for i in range(0, len(subfolder_codes), 500):
        batch = subfolder_codes[i:i + 500]
        ph = ",".join(["?"] * len(batch))
        cur.execute(f"SELECT Twr_Kod FROM CDN.TwrKarty WHERE Twr_Kod IN ({ph})", batch)
        codes.extend(r[0] for r in cur.fetchall())

    print(f"Subfolders in tree: {len(subfolder_codes)}, valid products: {len(codes)}")
    return codes


# --- 2. Fetch product data with price list ---

def fetch_products(cur, codes: list[str], pricelist: str,
                   fallback_pricelist: str | None = None) -> list[dict]:
    """Fetch product data from vKatalogProdukty for given codes and price list."""
    best = {}
    for i in range(0, len(codes), 500):
        batch = codes[i:i + 500]
        ph = ",".join(["?"] * len(batch))
        cur.execute(f"""
            SELECT {PRODUCT_COLUMNS}
            FROM AIOP.vKatalogProdukty
            WHERE KodXL IN ({ph})
              AND CennikNazwa = ?
        """, *batch, pricelist)
        cols = [c[0] for c in cur.description]
        for row in cur.fetchall():
            d = _row_to_dict(cols, row)
            code = d["KodXL"]
            if code not in best:
                best[code] = d

    # Fallback price list for missing products
    if fallback_pricelist:
        missing = [c for c in codes if c not in best]
        if missing:
            print(f"Fallback '{fallback_pricelist}' for {len(missing)} missing products...")
            for i in range(0, len(missing), 500):
                batch = missing[i:i + 500]
                ph = ",".join(["?"] * len(batch))
                cur.execute(f"""
                    SELECT {PRODUCT_COLUMNS}
                    FROM AIOP.vKatalogProdukty
                    WHERE KodXL IN ({ph})
                      AND CennikNazwa = ?
                """, *batch, fallback_pricelist)
                cols = [c[0] for c in cur.description]
                for row in cur.fetchall():
                    d = _row_to_dict(cols, row)
                    code = d["KodXL"]
                    if code not in best:
                        best[code] = d

    return list(best.values())


# --- 3. Default group resolution ---

SUB_CAT_PARENTS = {10, 11, 185, 12, 19}  # 1_ZNICZE, 2_WKŁADY, 3_LAMPIONY, 4_DEKORACJE, 5_ZNICZOMATY
MAIN_CAT_IDS = {1, 2}  # 01_CMENTARZ, 02_DOM


def resolve_default_groups(cur, products: list[dict]) -> None:
    """Add GrupaDomyslna field to each product based on ERP group tree."""
    gid_to_code = {p["TwrGIDNumer"]: p["KodXL"] for p in products}
    gids = list(gid_to_code.keys())
    group_map = {}

    for i in range(0, len(gids), 500):
        batch = gids[i:i + 500]
        ph = ",".join(["?"] * len(batch))
        cur.execute(f"""
            SELECT d.TGD_GIDNumer, g.TwG_Kod, g.TwG_GrONumer,
                   pg.TwG_Kod AS ParentKod, pg.TwG_GrONumer AS GrandparentId
            FROM CDN.TwrGrupyDom d
            JOIN CDN.TwrGrupy g ON d.TGD_GrONumer = g.TwG_GIDNumer
            LEFT JOIN CDN.TwrGrupy pg ON g.TwG_GrONumer = pg.TwG_GIDNumer
            WHERE d.TGD_GIDNumer IN ({ph})
        """, batch)
        for row in cur.fetchall():
            gid_num, grp_kod, grp_parent = row[0], row[1], row[2]
            if gid_num not in gid_to_code:
                continue
            code = gid_to_code[gid_num]
            if code in group_map:
                continue
            if grp_parent in SUB_CAT_PARENTS:
                group_map[code] = grp_kod
            elif grp_parent in MAIN_CAT_IDS:
                group_map[code] = grp_kod

    for p in products:
        p["GrupaDomyslna"] = group_map.get(p["KodXL"])


# --- 4. Packages ---

def fetch_packages(cur) -> list[dict]:
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
            "kod": row[2], "nazwa": row[3],
            "ilosc_szt": int(row[4]) if row[4] else 0,
        })
    return list(pkgs.values())


# --- 5. Save ---

def save_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Export catalog from ERP by folder")
    parser.add_argument("--folder", help="Offer folder path, e.g. 'OFERTY/2026/BRICO DDD'")
    parser.add_argument("--pricelist", help="Price list name, e.g. 'Cennik Brico DDD'")
    parser.add_argument("--fallback", help="Fallback price list name (optional)")
    parser.add_argument("--output", help="Output directory (default: data/)", default="data")
    parser.add_argument("--config", help="YAML config file (alternative to CLI args)")
    args = parser.parse_args()

    # Load from config if provided
    if args.config:
        import yaml
        cfg_path = ROOT / args.config
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        erp_cfg = cfg.get("erp_source", {})
        folder = erp_cfg.get("folder", args.folder)
        pricelist = erp_cfg.get("pricelist", args.pricelist)
        fallback = erp_cfg.get("fallback_pricelist", args.fallback)
        out_dir = Path(cfg.get("data", {}).get("products_path", "data/catalog_products.json")).parent
        output = ROOT / out_dir
    else:
        folder = args.folder
        pricelist = args.pricelist
        fallback = args.fallback
        output = ROOT / args.output

    if not folder or not pricelist:
        parser.error("--folder and --pricelist are required (or use --config)")

    conn = _connect()
    cur = conn.cursor()

    # 1. Find products by folder
    codes = find_products_by_folder(cur, folder)
    if not codes:
        print("No products found in folder. Exiting.")
        conn.close()
        sys.exit(1)

    # 2. Fetch product data
    products = fetch_products(cur, codes, pricelist, fallback)
    print(f"Products with price: {len(products)}")

    # 3. Resolve default groups
    resolve_default_groups(cur, products)

    grp_stats = {}
    for p in products:
        g = p.get("GrupaDomyslna") or "(brak)"
        grp_stats[g] = grp_stats.get(g, 0) + 1
    print("Default groups:")
    for g in sorted(grp_stats, key=lambda x: grp_stats[x], reverse=True):
        print(f"  {g}: {grp_stats[g]}")

    # Set GrupaSciezka
    for p in products:
        p["GrupaSciezka"] = folder

    # 4. Packages
    packages = fetch_packages(cur)
    print(f"Packages: {len(packages)}")

    # Missing
    found_codes = set(p["KodXL"] for p in products)
    missing = [c for c in codes if c not in found_codes]
    print(f"Missing in price list: {len(missing)}")
    if missing:
        for m in missing[:20]:
            print(f"  {m}")

    conn.close()

    # 5. Save
    save_json({"count": len(products), "products": products},
              output / "catalog_products.json")
    save_json({"count": len(packages), "packages": packages},
              output / "catalog_packages.json")
    print(f"Saved to {output}")

    with_price = sum(1 for p in products if (p.get("CenaNetto") or 0) > 0)
    print(f"With price > 0: {with_price}/{len(products)}")

    result = {
        "ok": True,
        "folder": folder,
        "pricelist": pricelist,
        "products": len(products),
        "packages": len(packages),
        "missing": len(missing),
        "with_price": with_price,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

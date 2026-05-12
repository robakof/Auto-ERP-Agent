"""
Catalog Export — eksport produktów, pakietów i zdjęć z ERP XL do plików JSON/JPG.

Opcjonalnie generuje formularz zamówieniowy Excel.

Usage:
    py tools/catalog_export.py --grupa "OFERTY/2025/BRICO"
    py tools/catalog_export.py --grupa "OFERTY/2025/BRICO" --render-excel
    py tools/catalog_export.py --grupa "OFERTY/2025/BRICO" --cennik-rodzaj 4 --photos
    py tools/catalog_export.py --render-excel --skip-export
"""

import argparse
import json
import os
import shutil
import sys
from decimal import Decimal
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

# ---------- Config ----------

SQL_SERVER = os.getenv("SQL_SERVER", "")
SQL_DATABASE = os.getenv("SQL_DATABASE", "")
SQL_USERNAME = os.getenv("SQL_USERNAME", "")
SQL_PASSWORD = os.getenv("SQL_PASSWORD", "")
SQL_DRIVER = "ODBC Driver 17 for SQL Server"

DATA_DIR = PROJECT_ROOT / "data"
IMAGES_DIR = PROJECT_ROOT / "assets" / "catalog" / "images"


# ---------- DB ----------

def _get_connection() -> pyodbc.Connection:
    conn_str = (
        f"DRIVER={{{SQL_DRIVER}}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USERNAME};"
        f"PWD={SQL_PASSWORD};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=30)


def _query_rows(conn, sql: str, params: list | None = None) -> list[dict]:
    cursor = conn.cursor()
    cursor.execute(sql, params or [])
    columns = [col[0] for col in cursor.description]
    rows = []
    for row in cursor.fetchall():
        d = {}
        for i, val in enumerate(row):
            if isinstance(val, Decimal):
                val = float(val)
            d[columns[i]] = val
        rows.append(d)
    return rows


# ---------- Export: Products ----------

def export_products(conn, grupa: str, cennik_rodzaj: int | None) -> list[dict]:
    """Export products from AIOP.vKatalogProdukty.

    Default (no cennik_rodzaj): one row per product with MAX(CenaNetto).
    With cennik_rodzaj: rows from that specific price list.
    """
    conditions = []
    params = []

    if cennik_rodzaj is not None:
        conditions.append("CennikRodzaj = ?")
        params.append(cennik_rodzaj)

    if grupa:
        conditions.append("GrupaSciezka LIKE ?")
        params.append(f"%{grupa}%")

    where = " AND ".join(conditions) if conditions else "1=1"

    if cennik_rodzaj is not None:
        sql = f"SELECT * FROM AIOP.vKatalogProdukty WHERE {where} ORDER BY KodXL"
    else:
        # One row per product: highest CenaNetto wins
        sql = f"""
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (
                    PARTITION BY KodXL ORDER BY CenaNetto DESC
                ) AS _rn
                FROM AIOP.vKatalogProdukty WHERE {where}
            ) ranked WHERE _rn = 1 ORDER BY KodXL
        """
    return _query_rows(conn, sql, params)


# ---------- Export: Packages ----------

def export_packages(conn) -> list[dict]:
    """Export packages from AIOP.vKatalogPakiety, grouped by parent."""
    rows = _query_rows(
        conn,
        "SELECT PakietKod, PakietNazwa, ProduktKod, ProduktNazwa, IloscSzt "
        "FROM AIOP.vKatalogPakiety ORDER BY PakietKod, ProduktKod"
    )
    packages = {}
    for r in rows:
        kod = r["PakietKod"]
        if kod not in packages:
            packages[kod] = {
                "pakiet_kod": kod,
                "pakiet_nazwa": r["PakietNazwa"],
                "skladniki": [],
            }
        packages[kod]["skladniki"].append({
            "kod": r["ProduktKod"],
            "nazwa": r["ProduktNazwa"],
            "ilosc_szt": r["IloscSzt"],
        })
    return list(packages.values())


# ---------- Export: Photos (from server disk) ----------

DEFAULT_PHOTOS_DIR = r"C:\CEIM\Zdjęcia"


def export_photos(conn, product_codes: list[str],
                  photos_dir: str = DEFAULT_PHOTOS_DIR) -> dict:
    """Copy product photos from server disk to assets/catalog/images/{KodXL}.jpg.

    Source files on disk are named by KodXL (e.g. DAVP43567.jpg).
    Output files keep the same KodXL naming.
    """
    if not product_codes:
        return {"exported": 0, "skipped": 0, "no_file": 0}

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    src_dir = Path(photos_dir)

    if not src_dir.exists():
        print(f"  WARNING: Photos directory not found: {src_dir}")
        return {"exported": 0, "skipped": 0, "no_file": len(product_codes)}

    # Build index of source files: KodXL (uppercase) → path
    src_index: dict[str, Path] = {}
    for f in src_dir.iterdir():
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        stem = f.stem.upper()
        if stem not in src_index:
            src_index[stem] = f

    # Copy photos: {KodXL}.jpg → {KodXL}.jpg
    exported = 0
    skipped = 0
    no_file = 0

    for kod in product_codes:
        kod_upper = kod.strip().upper()
        src_path = src_index.get(kod_upper)
        if not src_path:
            no_file += 1
            continue

        out_path = IMAGES_DIR / f"{kod_upper}.jpg"
        try:
            shutil.copy2(str(src_path), str(out_path))
            exported += 1
        except OSError as e:
            print(f"  WARNING: Failed to copy {src_path} → {out_path}: {e}")
            skipped += 1

    return {
        "exported": exported,
        "skipped": skipped,
        "no_file": no_file,
    }


# ---------- Save JSON ----------

def _save_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


# ---------- Render Excel ----------

def render_excel(config_path: str) -> dict:
    """Run Excel renderer using config YAML."""
    import yaml
    from tools.catalog.data_loader import load_erp_data
    from tools.catalog.renderers import render_excel as _render

    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    products, packages = load_erp_data(
        str(PROJECT_ROOT / config["data"]["products_path"]),
        str(PROJECT_ROOT / config["data"]["packages_path"]),
        config["data"].get("package_filter"),
    )

    output_path = config.get("outputs", {}).get("excel", {}).get("path", "output/zamowienie.xlsx")
    full_path = _render(products, packages, config, str(PROJECT_ROOT / output_path))

    return {
        "output": full_path,
        "products": len(products),
        "packages": len(packages),
        "size_kb": round(Path(full_path).stat().st_size / 1024, 1),
    }


# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(description="Catalog Export — SQL → JSON + photos + Excel")
    parser.add_argument("--grupa", default="", help="Filter by GrupaSciezka (LIKE), e.g. OFERTY/2025/BRICO")
    parser.add_argument("--cennik-rodzaj", type=int, default=None, help="Price list type (4=BRICO)")
    parser.add_argument("--photos", action="store_true", help="Copy product photos from server disk as EAN.jpg")
    parser.add_argument("--photos-dir", default=DEFAULT_PHOTOS_DIR, help="Source directory for product photos (default: C:\\CEIM\\Zdjęcia)")
    parser.add_argument("--render-excel", action="store_true", help="Generate Excel order form after export")
    parser.add_argument("--config", default="config/ceim_brico_2026.yaml", help="YAML config for Excel render")
    parser.add_argument("--skip-export", action="store_true", help="Skip SQL export, only render Excel from existing JSONs")
    parser.add_argument("--products-out", default="data/catalog_products.json", help="Output path for products JSON")
    parser.add_argument("--packages-out", default="data/catalog_packages.json", help="Output path for packages JSON")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    result = {"ok": True}

    if not args.skip_export:
        print(f"Connecting to {SQL_SERVER}/{SQL_DATABASE}...")
        conn = _get_connection()
        try:
            # Products
            print(f"Exporting products (grupa={args.grupa or 'ALL'}, cennik={args.cennik_rodzaj or 'default'})...")
            products = export_products(conn, args.grupa, args.cennik_rodzaj)
            products_path = PROJECT_ROOT / args.products_out
            _save_json({"count": len(products), "products": products}, products_path)
            result["products"] = {"count": len(products), "path": str(products_path)}
            print(f"  → {len(products)} products → {products_path}")

            # Packages
            print("Exporting packages...")
            packages = export_packages(conn)
            packages_path = PROJECT_ROOT / args.packages_out
            _save_json({"count": len(packages), "packages": packages}, packages_path)
            result["packages"] = {"count": len(packages), "path": str(packages_path)}
            print(f"  → {len(packages)} packages → {packages_path}")

            # Photos (from server disk)
            if args.photos:
                codes = [p["KodXL"] for p in products if p.get("KodXL")]
                print(f"Copying photos for {len(codes)} products from {args.photos_dir}...")
                photo_result = export_photos(conn, codes, args.photos_dir)
                result["photos"] = photo_result
                print(f"  → {photo_result['exported']} exported, {photo_result['no_file']} no file on disk")
        finally:
            conn.close()

    if args.render_excel:
        config_path = str(PROJECT_ROOT / args.config)
        print(f"Rendering Excel from {args.config}...")
        excel_result = render_excel(config_path)
        result["excel"] = excel_result
        print(f"  → {excel_result['output']} ({excel_result['size_kb']} KB, {excel_result['products']} products, {excel_result['packages']} packages)")

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()

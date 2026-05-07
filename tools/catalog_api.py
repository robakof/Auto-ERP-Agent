"""
Catalog API — FastAPI server serving product data from AIOP SQL views.

Endpoints:
  GET /api/product/{kod}         — single product (all prices)
  GET /api/products?sezon=&cennik= — product list with filters
  GET /api/package/{kod}         — package composition
  GET /api/photo/{kod}           — product photo (binary)
  GET /api/price-lists           — available price lists

Auth: API key via X-API-Key header or ?api_key= query param.
Config: .env (SQL_*, CATALOG_API_KEY, CATALOG_API_PORT)
"""

import io
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pyodbc
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import APIKeyHeader, APIKeyQuery

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

# ---------- Config ----------

API_KEY = os.getenv("CATALOG_API_KEY", "ceim-katalog-2025")
API_PORT = int(os.getenv("CATALOG_API_PORT", "8502"))

SQL_SERVER = os.getenv("SQL_SERVER", "")
SQL_DATABASE = os.getenv("SQL_DATABASE", "")
SQL_USERNAME = os.getenv("SQL_USERNAME", "")
SQL_PASSWORD = os.getenv("SQL_PASSWORD", "")
SQL_DRIVER = "ODBC Driver 17 for SQL Server"

# ---------- DB ----------


def get_connection() -> pyodbc.Connection:
    conn_str = (
        f"DRIVER={{{SQL_DRIVER}}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USERNAME};"
        f"PWD={SQL_PASSWORD};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=30)


def query_rows(sql: str, params: list | None = None) -> list[dict]:
    conn = get_connection()
    try:
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
    finally:
        conn.close()


def query_one(sql: str, params: list | None = None) -> dict | None:
    rows = query_rows(sql, params)
    return rows[0] if rows else None


# ---------- Auth ----------

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def verify_api_key(
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query),
):
    key = header_key or query_key
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return key


# ---------- App ----------

app = FastAPI(
    title="CEiM Catalog API",
    version="1.0.0",
    description="Product data from Comarch XL (AIOP views)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ---------- Endpoints ----------


@app.get("/api/product/{kod}", dependencies=[Depends(verify_api_key)])
def get_product(kod: str):
    """Single product — all attributes + all prices."""
    rows = query_rows(
        "SELECT * FROM AIOP.vKatalogProdukty WHERE KodXL = ?", [kod]
    )
    if not rows:
        raise HTTPException(404, f"Product {kod} not found")

    # Base data (same for all rows)
    base = rows[0]
    product = {
        "kod": base["KodXL"],
        "ean": base["KodEAN"],
        "nazwa": base["NazwaHandlowa"],
        "grupa": (base.get("GrupaSciezka") or "").strip(),
        "sezon": (base.get("Sezon") or "").strip(),
        "kolor": (base.get("Kolor") or "").strip(),
        "status_ofertowy": (base.get("StatusOfertowy") or "").strip(),
        "czas_palenia_h": base.get("CzasPalenia_h"),
        "gramatura_g": base.get("GramaturaWkladu_g"),
        "wysokosc_netto_cm": base.get("WysokoscNetto_cm"),
        "szerokosc_netto_cm": base.get("SzerokoscNetto_cm"),
        "srednica_cm": base.get("SrednicaProduktu_cm"),
        "material": (base.get("Material") or "").strip(),
        "zapach": (base.get("Zapach") or "").strip(),
        "waga_g": base.get("WagaProduktu_g"),
        "srednica_otworu_cm": base.get("SrednicaOtworu_cm"),
        "szerokosc_brutto_cm": base.get("SzerokoscBrutto_cm"),
        "wysokosc_brutto_cm": base.get("WysokoscBrutto_cm"),
        "glebokosc_brutto_cm": base.get("GlebokoscBrutto_cm"),
        "szt_w_opakowaniu": base.get("SztWOpakowaniu"),
        "szt_na_warstwie": base.get("SztNaWarstwie"),
        "szt_na_palecie": base.get("SztNaPalecie"),
        "ma_zdjecie": bool(base.get("MaZdjecie")),
        "liczba_zdjec": base.get("LiczbaZdjec", 0),
        "zasilanie": (base.get("Zasilanie") or "").strip(),
        "bateria_w_zestawie": (base.get("CzyBateriaWZestawie") or "").strip(),
        "ceny": [],
    }

    # Prices (one per row)
    for row in rows:
        if row.get("CennikId") is not None:
            product["ceny"].append({
                "cennik_id": row["CennikId"],
                "cennik_nazwa": (row.get("CennikNazwa") or "").strip(),
                "cennik_rodzaj": row.get("CennikRodzaj"),
                "cena_netto": row.get("CenaNetto"),
                "waluta": (row.get("CenaWaluta") or "PLN").strip(),
            })

    return product


@app.get("/api/products", dependencies=[Depends(verify_api_key)])
def list_products(
    sezon: Optional[str] = Query(None, description="Filter by Sezon"),
    grupa: Optional[str] = Query(None, description="Filter by GrupaSciezka (LIKE)"),
    cennik_rodzaj: Optional[int] = Query(None, description="Price list type (4=BRICO)"),
    limit: int = Query(500, ge=1, le=10000),
):
    """Product list with optional filters. One row per product."""
    conditions = []
    params = []

    if cennik_rodzaj is not None:
        conditions.append("CennikRodzaj = ?")
        params.append(cennik_rodzaj)
    else:
        conditions.append("CennikId IS NULL")

    if sezon:
        conditions.append("Sezon LIKE ?")
        params.append(f"%{sezon}%")

    if grupa:
        conditions.append("GrupaSciezka LIKE ?")
        params.append(f"%{grupa}%")

    where = " AND ".join(conditions) if conditions else "1=1"
    sql = f"SELECT TOP {limit} * FROM AIOP.vKatalogProdukty WHERE {where} ORDER BY KodXL"

    rows = query_rows(sql, params)
    return {"count": len(rows), "products": rows}


@app.get("/api/package/{kod}", dependencies=[Depends(verify_api_key)])
def get_package(kod: str):
    """Package composition — parent + child products."""
    rows = query_rows(
        "SELECT * FROM AIOP.vKatalogPakiety WHERE PakietKod = ?", [kod]
    )
    if not rows:
        raise HTTPException(404, f"Package {kod} not found")

    return {
        "pakiet_kod": rows[0]["PakietKod"],
        "pakiet_nazwa": rows[0]["PakietNazwa"],
        "skladniki": [
            {
                "kod": r["ProduktKod"],
                "nazwa": r["ProduktNazwa"],
                "ilosc_szt": r["IloscSzt"],
            }
            for r in rows
        ],
    }


@app.get("/api/packages", dependencies=[Depends(verify_api_key)])
def list_packages(
    sezon: Optional[str] = Query(None, description="Filter by year, e.g. 2025"),
):
    """List all packages (optionally filtered by year in code)."""
    if sezon:
        rows = query_rows(
            "SELECT DISTINCT PakietKod, PakietNazwa FROM AIOP.vKatalogPakiety "
            "WHERE PakietKod LIKE ? ORDER BY PakietKod",
            [f"%{sezon}%"],
        )
    else:
        rows = query_rows(
            "SELECT DISTINCT PakietKod, PakietNazwa FROM AIOP.vKatalogPakiety "
            "ORDER BY PakietKod"
        )
    return {"count": len(rows), "packages": rows}


@app.get("/api/photo/{kod}", dependencies=[Depends(verify_api_key)])
def get_photo(kod: str, index: int = Query(0, ge=0, description="Photo index")):
    """Product photo as binary image (JPG/PNG)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT dab.DAB_Dane, dab.DAB_Rozszerzenie "
            "FROM CDN.DaneObiekty dao "
            "INNER JOIN CDN.DaneBinarne dab ON dao.DAO_DABId = dab.DAB_ID "
            "WHERE dao.DAO_ObiTyp = 16 "
            "  AND dao.DAO_ObiNumer = (SELECT Twr_GIDNumer FROM CDN.TwrKarty WHERE Twr_Kod = ?) "
            "  AND dab.DAB_Rozszerzenie IN ('jpg','png','jpeg','JPG','PNG','JPEG') "
            "ORDER BY dab.DAB_ID",
            [kod],
        )
        rows = cursor.fetchall()
        if not rows or index >= len(rows):
            raise HTTPException(404, f"Photo not found for {kod} (index={index})")

        data = rows[index][0]
        ext = rows[index][1].lower().strip()

        if data is None or len(data) == 0:
            raise HTTPException(404, f"Photo blob empty for {kod}")

        media_type = "image/png" if ext == "png" else "image/jpeg"
        return Response(content=bytes(data), media_type=media_type)
    finally:
        conn.close()


@app.get("/api/price-lists", dependencies=[Depends(verify_api_key)])
def list_price_lists():
    """Available price lists (cenniki)."""
    rows = query_rows(
        "SELECT TCN_Id, RTRIM(TCN_Nazwa) AS Nazwa, TCN_RodzajCeny AS Rodzaj "
        "FROM CDN.TwrCenyNag ORDER BY TCN_Id"
    )
    return {"count": len(rows), "price_lists": rows}


@app.get("/api/health")
def health():
    """Health check (no auth)."""
    try:
        conn = get_connection()
        conn.close()
        return {"status": "ok", "database": SQL_DATABASE}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ---------- Main ----------

if __name__ == "__main__":
    uvicorn.run(
        "catalog_api:app",
        host="0.0.0.0",
        port=API_PORT,
        reload=False,
    )

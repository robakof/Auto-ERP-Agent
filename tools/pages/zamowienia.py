"""
pages/zamowienia.py — Generator formularzy zamowieniowych.

Uproszczony UI: wybierz folder ofertowy z Comarch -> generuj Excel.
Dane pobierane przez catalog_export_erp.py (folder TwrGrupy + cennik).

Uruchamiana z menu glownego: streamlit run tools/app.py
"""

import json
import tempfile
import sys
from decimal import Decimal
from pathlib import Path

import streamlit as st
import yaml

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT))

from tools.catalog_export_erp import (
    _connect,
    find_products_by_folder,
    fetch_products,
    fetch_packages,
    resolve_default_groups,
    save_json,
)
from tools.catalog_export import export_photos, _get_connection

_CONFIG_DIR = _ROOT / "config" / "catalogs"
_DATA_DIR = _ROOT / "data"

st.set_page_config(page_title="Zamowienia", layout="wide")

if st.button("< Menu glowne"):
    st.switch_page("app.py")

st.markdown(
    "<h2 style='color:#1A1A1A; margin-bottom:4px;'>Generator Zamowien "
    "<span style='color:#FAA400'>CEiM</span></h2>",
    unsafe_allow_html=True,
)
st.markdown("<hr style='border:2px solid #FAA400; margin-top:0;'>", unsafe_allow_html=True)

st.info("Wybierz folder ofertowy z Comarch, kliknij Generuj - pobierz formularz Excel.")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@st.cache_data(ttl=300, show_spinner="Pobieranie drzewa ofert z Comarch...")
def fetch_offer_tree() -> dict:
    """Return {year: {client_name: product_count}} from TwrGrupy under 10_OFERTY."""
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute("SELECT TwG_GIDNumer FROM CDN.TwrGrupy WHERE TwG_Kod = '10_OFERTY'")
        root = cur.fetchone()
        if not root:
            return {}

        cur.execute(
            "SELECT TwG_GIDNumer, TwG_Kod FROM CDN.TwrGrupy "
            "WHERE TwG_GrONumer = ? ORDER BY TwG_Kod DESC", root[0]
        )
        years = cur.fetchall()

        tree = {}
        for y_id, y_kod in years:
            cur.execute(
                "SELECT TwG_GIDNumer, TwG_Kod FROM CDN.TwrGrupy "
                "WHERE TwG_GrONumer = ? ORDER BY TwG_Kod", y_id
            )
            clients = cur.fetchall()
            year_data = {}
            for c_id, c_kod in clients:
                cur.execute(
                    "SELECT COUNT(*) FROM CDN.TwrGrupy WHERE TwG_GrONumer = ?", c_id
                )
                cnt = cur.fetchone()[0]
                if cnt > 0:
                    year_data[c_kod] = cnt
            if year_data:
                tree[y_kod] = year_data
        return tree
    finally:
        conn.close()


@st.cache_data(ttl=300, show_spinner="Pobieranie cennikow z ERP...")
def fetch_pricelists() -> list[str]:
    """Return distinct pricelist names from AIOP.vKatalogProdukty."""
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT DISTINCT CennikNazwa FROM AIOP.vKatalogProdukty "
            "WHERE CennikNazwa IS NOT NULL ORDER BY CennikNazwa"
        )
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()


def _find_config_for_folder(folder_path: str) -> Path | None:
    """Find YAML config with matching erp_source.folder."""
    for cfg_file in _CONFIG_DIR.glob("*.yaml"):
        cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
        erp = cfg.get("erp_source", {})
        if erp.get("folder") == folder_path:
            return cfg_file
    return None


def generate_excel(config: dict, products_json: list, packages_json: list) -> bytes:
    from tools.catalog.data_loader import load_erp_data
    from tools.catalog.renderers import render_excel as _render

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        prod_path = tmp_path / "products.json"
        pkg_path = tmp_path / "packages.json"

        prod_path.write_text(
            json.dumps({"count": len(products_json), "products": products_json},
                       ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        pkg_path.write_text(
            json.dumps({"count": len(packages_json), "packages": packages_json},
                       ensure_ascii=False, default=str),
            encoding="utf-8",
        )

        products, packages = load_erp_data(
            str(prod_path), str(pkg_path),
            config.get("data", {}).get("package_filter"),
        )

        out_path = tmp_path / "zamowienie.xlsx"
        _render(products, packages, config, str(out_path))
        return out_path.read_bytes()


# ---------------------------------------------------------------------------
# Sidebar — wybor oferty z drzewa Comarch
# ---------------------------------------------------------------------------

st.sidebar.header("Folder ofertowy")

offer_tree = fetch_offer_tree()
year_list = list(offer_tree.keys())

if not year_list:
    st.sidebar.error("Brak folderow ofertowych w Comarch")
    st.stop()

selected_year = st.sidebar.selectbox("Rok", year_list, index=0)

clients = offer_tree.get(selected_year, {})
client_names = list(clients.keys())
client_labels = [f"{name} ({clients[name]} prod.)" for name in client_names]

if client_names:
    selected_idx = st.sidebar.selectbox(
        "Klient / Oferta",
        range(len(client_names)),
        format_func=lambda i: client_labels[i],
        index=0,
    )
    selected_client = client_names[selected_idx]
    folder_path = f"OFERTY/{selected_year}/{selected_client}"
else:
    folder_path = ""
    st.sidebar.warning("Brak ofert dla wybranego roku")

# --- Config auto-detection ---
st.sidebar.markdown("---")

matched_config = _find_config_for_folder(folder_path) if folder_path else None

yaml_files = sorted(_CONFIG_DIR.glob("*.yaml"))
config_names = [f.stem for f in yaml_files]
default_idx = 0
if matched_config:
    try:
        default_idx = config_names.index(matched_config.stem)
    except ValueError:
        pass

selected_config = st.sidebar.selectbox(
    "Konfiguracja Excel",
    config_names,
    index=default_idx,
)
config_path = _CONFIG_DIR / f"{selected_config}.yaml"
config = _load_config(config_path)

# --- Cennik (auto from config or manual) ---
erp_src = config.get("erp_source", {})
config_pricelist = erp_src.get("pricelist", "")
config_fallback = erp_src.get("fallback_pricelist", "")

all_pricelists = fetch_pricelists()

if config_pricelist and config_pricelist in all_pricelists:
    pricelist_idx = all_pricelists.index(config_pricelist)
else:
    pricelist_idx = 0

selected_pricelist = st.sidebar.selectbox(
    "Cennik",
    all_pricelists,
    index=pricelist_idx,
)

fallback_pricelist = st.sidebar.selectbox(
    "Cennik zapasowy (opcjonalnie)",
    ["(brak)"] + all_pricelists,
    index=(all_pricelists.index(config_fallback) + 1) if config_fallback in all_pricelists else 0,
)
if fallback_pricelist == "(brak)":
    fallback_pricelist = None

# --- Photos ---
copy_photos = st.sidebar.checkbox("Kopiuj zdjecia z serwera", value=True)

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Folder:** `{folder_path}`")
with col2:
    st.markdown(f"**Cennik:** `{selected_pricelist}`")

if st.button("Generuj zamowienie", type="primary", use_container_width=True):
    if not folder_path:
        st.error("Wybierz folder ofertowy.")
    else:
        conn = _connect()
        cur = conn.cursor()

        # 1. Find products by folder
        with st.spinner(f"Szukanie produktow w {folder_path}..."):
            codes = find_products_by_folder(cur, folder_path)

        if not codes:
            st.error("Brak produktow w wybranym folderze.")
            conn.close()
            st.stop()

        st.success(f"Znaleziono {len(codes)} produktow w folderze")

        # 2. Fetch product data with pricelist
        with st.spinner(f"Pobieranie danych z cennika '{selected_pricelist}'..."):
            products = fetch_products(cur, codes, selected_pricelist, fallback_pricelist)
            for p in products:
                for k, v in list(p.items()):
                    if isinstance(v, Decimal):
                        p[k] = float(v)

        st.success(f"Pobrano {len(products)} produktow z cenami")

        # 3. Resolve default groups
        with st.spinner("Rozwiazywanie grup domyslnych..."):
            resolve_default_groups(cur, products)
            for p in products:
                p["GrupaSciezka"] = folder_path

        # 4. Packages
        with st.spinner("Pobieranie pakietow..."):
            packages = fetch_packages(cur)

        st.success(f"Pobrano {len(packages)} pakietow")
        conn.close()

        # 5. Save JSONs
        save_json({"count": len(products), "products": products},
                  _DATA_DIR / "catalog_products.json")
        save_json({"count": len(packages), "packages": packages},
                  _DATA_DIR / "catalog_packages.json")

        # 6. Photos
        if copy_photos:
            with st.spinner("Kopiowanie zdjec z serwera..."):
                photo_codes = [p["KodXL"] for p in products if p.get("KodXL")]
                photo_conn = _get_connection()
                try:
                    photo_result = export_photos(photo_conn, photo_codes)
                finally:
                    photo_conn.close()
            st.success(
                f"Zdjecia: {photo_result['exported']} skopiowanych, "
                f"{photo_result['no_file']} brak na dysku, "
                f"{photo_result.get('no_ean', 0)} brak EAN"
            )

        # 7. Generate Excel
        with st.spinner("Generowanie Excel..."):
            excel_bytes = generate_excel(config, products, packages)

        st.success("Formularz zamowieniowy gotowy!")
        st.session_state["excel_bytes"] = excel_bytes
        st.session_state["excel_name"] = f"zamowienie_{folder_path.replace('/', '_')}.xlsx"

        # Stats
        with_price = sum(1 for p in products if (p.get("CenaNetto") or 0) > 0)
        missing = len(codes) - len(products)
        st.info(f"Z cena > 0: {with_price}/{len(products)} | Brak w cenniku: {missing}")

if "excel_bytes" in st.session_state:
    st.download_button(
        label="Pobierz Excel",
        data=st.session_state["excel_bytes"],
        file_name=st.session_state["excel_name"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

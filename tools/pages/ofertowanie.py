"""
pages/ofertowanie.py — Eksport ofertowania ERP do Excel.

Uruchamiana z menu głównego: streamlit run tools/app.py
"""

import tempfile
from datetime import date
from pathlib import Path
import sys

import streamlit as st

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT))

from tools.ofertowanie_export import (
    _export_excel, _find_photo, _sql_group, _sql_excel, _read_excel_codes,
    GROUP_NUMER, GROUP_TYP,
)
from tools.lib.sql_client import SqlClient

_OUTPUT_DIR = _ROOT / "output"

st.set_page_config(page_title="Ofertowanie", layout="centered")
st.markdown("<style>.block-container { max-width: 640px; }</style>", unsafe_allow_html=True)

if st.button("← Menu główne"):
    st.switch_page("app.py")

st.markdown(
    "<h2 style='color:#1A1A1A; margin-bottom:4px;'>Eksport Ofertowania "
    "<span style='color:#FAA400'>CEiM</span></h2>",
    unsafe_allow_html=True,
)
st.markdown("<hr style='border:2px solid #FAA400; margin-top:0;'>", unsafe_allow_html=True)

st.info("Generuje plik Excel z produktami ERP: zdjęcia, ceny, wymiary, opakowania.")


# --- Ładowanie grup z ERP (cache 5 min) ---
@st.cache_data(ttl=300, show_spinner="Ładowanie grup towarów z ERP…")
def fetch_groups():
    sql = (
        f"SELECT g2.TwG_GIDNumer, g1.TwG_Kod, g2.TwG_Kod, g2.TwG_Nazwa "
        f"FROM CDN.TwrGrupy g1 "
        f"JOIN CDN.TwrGrupy g2 ON g2.TwG_GrONumer = g1.TwG_GIDNumer AND g2.TwG_GIDTyp = {GROUP_TYP} "
        f"WHERE g1.TwG_GIDTyp = {GROUP_TYP} AND g1.TwG_GrONumer = {GROUP_NUMER} "
        f"ORDER BY g1.TwG_Kod, g2.TwG_Kod"
    )
    result = SqlClient().execute(sql, inject_top=None)
    if not result["ok"]:
        raise RuntimeError(result["error"]["message"])
    return [(r[0], f"{r[1]} / {r[2]} — {r[3]}") for r in result["rows"]]


# --- Źródło ---
source = st.radio("Źródło:", ["Z grupy ERP", "Z pliku Excel"], horizontal=True)

st.divider()

sql = None
output_name = f"ofertowanie_{date.today()}.xlsx"

if source == "Z grupy ERP":
    try:
        groups = fetch_groups()
    except Exception as e:
        st.error(f"Błąd połączenia z ERP: {e}")
        st.stop()

    group_numers = [numer for numer, _ in groups]
    group_labels = [label for _, label in groups]

    selected_idx = st.selectbox(
        "Grupa towarów:",
        range(len(group_labels)),
        format_func=lambda i: group_labels[i],
    )
    selected_numer = group_numers[selected_idx]
    selected_symbol = group_labels[selected_idx].split(" — ")[0].replace(" ", "_")
    output_name = f"ofertowanie_{selected_symbol}_{date.today()}.xlsx"
    sql = _sql_group(selected_numer)

else:
    st.caption("Plik Excel z kolumną 'Kod' lub kodami w pierwszej kolumnie.")
    uploaded = st.file_uploader("Wybierz plik .xlsx", type=["xlsx", "xls"])
    if uploaded:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name
        kody = _read_excel_codes(tmp_path)
        if not kody:
            st.error("Brak kodów w pliku.")
            st.stop()
        sql = _sql_excel(kody)
        output_name = f"ofertowanie_{Path(uploaded.name).stem}_{date.today()}.xlsx"

st.divider()

xlsx_bytes = None

if st.button("Generuj Excel", type="primary", use_container_width=True):
    if not sql:
        st.error("Wybierz źródło danych.")
        st.stop()

    with st.spinner("Pobieranie danych z ERP…"):
        try:
            result = SqlClient().execute(sql, inject_top=None)
            if not result["ok"]:
                st.error(f"Błąd ERP: {result['error']['message']}")
                st.stop()

            columns = result["columns"]
            db_rows = result["rows"]

            rows = []
            for db_row in db_rows:
                row = dict(zip(columns, db_row))
                kod = row.get("Kod", "")
                filename, zaladowane, has_png = _find_photo(kod)
                row["Zdjęcie"] = filename
                row["Czy zdjęcie załadowane do systemu"] = "Tak" if zaladowane else "Nie"
                row["Czy zdjęcie zrobione png"] = "Tak" if has_png else "Nie"
                rows.append(row)

            if not rows:
                st.warning("Brak produktów dla wybranego źródła.")
                st.stop()

            _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            out_path = _OUTPUT_DIR / output_name
            _export_excel(rows, str(out_path))
            xlsx_bytes = out_path.read_bytes()
            st.success(f"OK — {len(rows)} produktów.")

        except Exception as e:
            st.error(f"Błąd: {e}")
            st.stop()

if xlsx_bytes:
    st.download_button(
        label="Pobierz Excel (.xlsx)",
        data=xlsx_bytes,
        file_name=output_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

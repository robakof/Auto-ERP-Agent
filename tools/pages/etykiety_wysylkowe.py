"""
pages/etykiety_wysylkowe.py — Generator etykiet wysyłkowych Word.

Uruchamiana z menu głównego: streamlit run tools/app.py
"""

import tempfile
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(_ROOT))

from tools.etykiety_export import generate, _query_products, _query_products_from_codes, load_codes_from_excel
from tools.lib.sql_client import SqlClient

_SQL_GRUPY = _ROOT / "solutions" / "jas" / "etykiety_grupy.sql"
_OUTPUT_DIR = _ROOT / "output"

st.set_page_config(page_title="Etykiety Wysyłkowe", layout="centered")

st.markdown("<style>.block-container { max-width: 640px; }</style>", unsafe_allow_html=True)

# Powrót do menu
if st.button("← Menu główne"):
    st.switch_page("app.py")

st.markdown(
    "<h2 style='color:#1A1A1A; margin-bottom:4px;'>Etykiety Wysyłkowe</h2>",
    unsafe_allow_html=True,
)
st.markdown("<hr style='border:2px solid #FAA400; margin-top:0;'>", unsafe_allow_html=True)

st.info("Z ERP: wybierz rok i klienta. Z pliku Excel: plik musi zawierać kolumnę **'Kod'** z kodami produktów (pierwszy wiersz = nagłówek). Pobierz Word.")

# --- Ładowanie grup z ERP (cache 5 min) ---
@st.cache_data(ttl=300, show_spinner="Ładowanie listy klientów z ERP…")
def fetch_grupy():
    sql = _SQL_GRUPY.read_text(encoding="utf-8")
    result = SqlClient().execute(sql, inject_top=None)
    if not result["ok"]:
        raise RuntimeError(result["error"]["message"])
    grupy = {}
    for row in result["rows"]:
        rok_gid, rok_kod, klient_gid, klient_kod = row
        grupy.setdefault(rok_kod, []).append((klient_kod, int(klient_gid)))
    for rok in grupy:
        grupy[rok].sort(key=lambda x: x[0])
    return dict(sorted(grupy.items(), reverse=True))


# --- Źródło danych ---
source = st.radio(
    "Źródło:",
    ["Z ERP (rok / klient)", "Z pliku Excel"],
    horizontal=True,
)

st.divider()

docx_bytes = None
output_name = "etykiety.docx"

# --- Tryb ERP ---
if source == "Z ERP (rok / klient)":
    try:
        grupy = fetch_grupy()
    except Exception as e:
        st.error(f"Błąd połączenia z ERP: {e}")
        st.stop()

    if not grupy:
        st.warning("Brak danych w ERP.")
        st.stop()

    rok = st.selectbox("Rok:", list(grupy.keys()))
    klienci = grupy.get(rok, [])
    klient_kod = st.selectbox("Klient:", [k for k, _ in klienci])
    klient_gid = next((gid for kod, gid in klienci if kod == klient_kod), None)
    output_name = f"etykiety_{rok}_{klient_kod.replace(' ', '_')}.docx"

    st.divider()

    if st.button("Generuj etykiety", type="primary", use_container_width=True):
        with st.spinner(f"Pobieranie danych dla {klient_kod} {rok}…"):
            try:
                products = _query_products(klient_gid)
                if not products:
                    st.error(f"Brak produktów dla {klient_kod} {rok}.")
                    st.stop()
                _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                out_path = _OUTPUT_DIR / output_name
                generate(products, out_path)
                docx_bytes = out_path.read_bytes()
                st.success(f"OK — {len(products)} etykiet wygenerowanych.")
            except Exception as e:
                st.error(f"Błąd: {e}")
                st.stop()

# --- Tryb Excel ---
else:
    uploaded = st.file_uploader("Plik z kodami produktów (.xlsx, kolumna 'Kod'):", type=["xlsx", "xls"])

    st.divider()

    if st.button("Generuj etykiety", type="primary", use_container_width=True):
        if not uploaded:
            st.error("Wgraj plik Excel z kodami.")
            st.stop()
        with st.spinner("Wczytywanie kodów i pobieranie danych z ERP…"):
            try:
                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                    tmp.write(uploaded.read())
                    excel_path = tmp.name
                kody = load_codes_from_excel(excel_path)
                if not kody:
                    st.error("Brak kodów w pliku.")
                    st.stop()
                products = _query_products_from_codes(kody)
                if not products:
                    st.error("Brak danych w ERP dla podanych kodów.")
                    st.stop()
                output_name = f"etykiety_{Path(uploaded.name).stem}.docx"
                _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                out_path = _OUTPUT_DIR / output_name
                generate(products, out_path)
                docx_bytes = out_path.read_bytes()
                st.success(f"OK — {len(products)} etykiet wygenerowanych.")
            except Exception as e:
                st.error(f"Błąd: {e}")
                st.stop()

# --- Pobieranie ---
if docx_bytes:
    st.download_button(
        label="Pobierz plik Word (.docx)",
        data=docx_bytes,
        file_name=output_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )

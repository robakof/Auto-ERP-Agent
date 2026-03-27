"""
pages/oferta_katalogowa_3x3.py — Generator ofert katalogowych PDF (wariant 3×3).

Uruchamiana z menu głównego: streamlit run tools/app.py
"""

import tempfile
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(_ROOT))

from tools.offer_data import load_products
from tools.offer_pdf_3x3 import generate_pdf

_DEFAULT_INPUT = _ROOT / "documents" / "Wzory plików" / "OFerta katalogowa.xlsx"
_DEFAULT_OUTPUT = _ROOT / "output" / "oferta_katalogowa_3x3.pdf"

st.set_page_config(page_title="Oferta Katalogowa 3×3", layout="centered")

st.markdown("""
<style>
    .block-container { max-width: 640px; }
</style>
""", unsafe_allow_html=True)

# Powrót do menu
if st.button("← Menu główne"):
    st.switch_page("app.py")

# --- Nagłówek ---
st.markdown(
    "<h2 style='color:#1A1A1A; margin-bottom:4px;'>Generator Oferty Katalogowej "
    "<span style='color:#FAA400'>CEiM</span> "
    "<span style='font-size:0.8em; color:#6B6B6B;'>3×3</span></h2>",
    unsafe_allow_html=True,
)
st.markdown("<hr style='border:2px solid #FAA400; margin-top:0;'>", unsafe_allow_html=True)

st.info("Excel musi zawierać kolumny **'Akronim produktu'** i **'Cena sprzedaży'** w pierwszym wierszu. Wybierz logo i nagłówek — kliknij Generuj PDF.")

# --- Plik wejściowy ---
st.subheader("Plik produktów (Excel)")
uploaded = st.file_uploader("Wybierz plik .xlsx", type=["xlsx", "xls"])
excel_bytes = uploaded.read() if uploaded else None

st.divider()

# --- Parametry ---
logo = st.radio("Logo", ["CEiM", "KERTI"], horizontal=True).lower()

header_text = st.text_input("Nagłówek", placeholder="Wkłady zniczowe CEiM")

st.divider()

# --- Generowanie ---
if st.button("Generuj PDF", type="primary", use_container_width=True):

    if not excel_bytes:
        st.error("Wgraj plik Excel przed generowaniem.")
        st.stop()

    with st.spinner("Generowanie PDF…"):
        try:
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(excel_bytes)
                input_path = tmp.name

            _DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            products = load_products(input_path, lang="pl")
            generate_pdf(
                products,
                str(_DEFAULT_OUTPUT),
                lang="pl",
                header_text=header_text.strip() or None,
                logo=logo,
            )
            pdf_bytes = _DEFAULT_OUTPUT.read_bytes()

        except Exception as e:
            st.error(f"Błąd: {e}")
            st.stop()

    st.success("PDF gotowy — zapisany w `output/oferta_katalogowa_3x3.pdf`")
    st.download_button(
        label="Pobierz PDF",
        data=pdf_bytes,
        file_name="oferta_katalogowa_3x3.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

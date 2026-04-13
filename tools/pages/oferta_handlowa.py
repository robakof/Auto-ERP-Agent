"""
pages/oferta_handlowa.py — Generator oferty handlowej szkła Kerti (design FINAL28).

Uruchamiana z menu głównego: streamlit run tools/app.py
"""

import tempfile
import traceback
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(_ROOT))

from tools.offer_kerti_data import load_kerti_products
from tools.offer_kerti_html import generate_html
from tools.offer_kerti_pdf import html_to_pdf

_DEFAULT_OUTPUT = _ROOT / "output" / "oferta_handlowa_kerti.pdf"

st.set_page_config(page_title="Oferta Handlowa Kerti", layout="centered")

st.markdown("""
<style>
    .block-container { max-width: 640px; }
</style>
""", unsafe_allow_html=True)

if st.button("← Menu główne"):
    st.switch_page("app.py")

st.markdown(
    "<h2 style='color:#1A1A1A; margin-bottom:4px;'>Generator Oferty Handlowej "
    "<span style='color:#BD7E4D'>Kerti</span></h2>",
    unsafe_allow_html=True,
)
st.markdown("<hr style='border:2px solid #BD7E4D; margin-top:0;'>", unsafe_allow_html=True)

st.info(
    "Excel musi zawierać kolumnę **'Akronim produktu'** "
    "(+ opcjonalnie **'Nowość'** TRUE/FALSE). "
    "Dane parametrów pobierane są automatycznie z ERP."
)

st.subheader("Plik produktów (Excel)")
uploaded = st.file_uploader("Wybierz plik .xlsx", type=["xlsx", "xls"])
excel_bytes = uploaded.read() if uploaded else None

st.divider()

layout = st.radio("Layout siatki", ["g2", "g3", "g4"], index=1, horizontal=True)

st.divider()

if st.button("Generuj PDF", type="primary", use_container_width=True):

    if not excel_bytes:
        st.error("Wgraj plik Excel przed generowaniem.")
        st.stop()

    with st.spinner("Pobieranie danych z ERP i generowanie PDF…"):
        try:
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(excel_bytes)
                input_path = tmp.name

            products = load_kerti_products(input_path)
            html = generate_html(products, layout=layout)

            _DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            html_to_pdf(html, str(_DEFAULT_OUTPUT))
            pdf_bytes = _DEFAULT_OUTPUT.read_bytes()

        except Exception as e:
            st.error(f"Błąd: {type(e).__name__}: {e}")
            st.code(traceback.format_exc(), language="text")
            st.stop()

    st.success("PDF gotowy — zapisany w `output/oferta_handlowa_kerti.pdf`")
    st.download_button(
        label="Pobierz PDF",
        data=pdf_bytes,
        file_name="oferta_handlowa_kerti.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

"""
offer_app_3x3.py — Przeglądarkowy interfejs generatora ofert katalogowych PDF (wariant 3×3).

Uruchomienie:
    streamlit run tools/offer_app_3x3.py
"""

import io
import sys
import tempfile
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.offer_data import load_products
from tools.offer_pdf_3x3 import generate_pdf

_PROJECT_ROOT = Path(__file__).parent.parent
_DEFAULT_INPUT = _PROJECT_ROOT / "documents" / "Wzory plików" / "OFerta katalogowa.xlsx"
_DEFAULT_OUTPUT = _PROJECT_ROOT / "output" / "oferta_katalogowa_3x3.pdf"

LANGUAGES = {"Polski": "pl", "English": "en", "Română": "ro"}

st.set_page_config(page_title="Generator Oferty 3×3", layout="centered")

st.markdown("""
<style>
    .block-container { max-width: 640px; }
    div[data-testid="stHorizontalBlock"] { align-items: center; }
</style>
""", unsafe_allow_html=True)

# --- Nagłówek ---
st.markdown(
    "<h2 style='color:#1A1A1A; margin-bottom:4px;'>Generator Oferty Katalogowej "
    "<span style='color:#FAA400'>CEiM</span> <span style='font-size:0.8em; color:#6B6B6B;'>3×3</span></h2>",
    unsafe_allow_html=True,
)
st.markdown("<hr style='border:2px solid #FAA400; margin-top:0;'>", unsafe_allow_html=True)

# --- Plik wejściowy ---
st.subheader("Plik produktów (Excel)")
use_upload = st.radio(
    "Źródło pliku:",
    ["Domyślny plik projektu", "Wgraj własny plik"],
    horizontal=True,
    label_visibility="collapsed",
)

excel_bytes = None
excel_name = None

if use_upload == "Wgraj własny plik":
    uploaded = st.file_uploader("Wybierz plik .xlsx", type=["xlsx", "xls"])
    if uploaded:
        excel_bytes = uploaded.read()
        excel_name = uploaded.name
else:
    if _DEFAULT_INPUT.exists():
        st.caption(f"Używa: `{_DEFAULT_INPUT}`")
    else:
        st.warning(f"Domyślny plik nie istnieje: `{_DEFAULT_INPUT}`")

st.divider()

# --- Parametry ---
col1, col2 = st.columns(2)
with col1:
    lang_label = st.selectbox("Język", list(LANGUAGES.keys()))
    lang = LANGUAGES[lang_label]
with col2:
    logo = st.radio("Logo", ["CEiM", "KERTI"], horizontal=True).lower()

header_text = st.text_input("Nagłówek", value="Wkłady zniczowe CEiM")

st.divider()

# --- Generowanie ---
if st.button("Generuj PDF", type="primary", use_container_width=True):

    # Walidacja
    has_input = (use_upload == "Domyślny plik projektu" and _DEFAULT_INPUT.exists()) or (excel_bytes is not None)
    if not has_input:
        st.error("Brak pliku wejściowego. Wgraj plik lub upewnij się że domyślny istnieje.")
        st.stop()

    with st.spinner("Generowanie PDF…"):
        try:
            # Przygotuj plik wejściowy
            if excel_bytes is not None:
                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_in:
                    tmp_in.write(excel_bytes)
                    input_path = tmp_in.name
            else:
                input_path = str(_DEFAULT_INPUT)

            # Generuj do bufora (do pobrania) i do pliku (lokalny output)
            _DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            output_path = str(_DEFAULT_OUTPUT)

            products = load_products(input_path, lang=lang)
            generate_pdf(
                products,
                output_path,
                lang=lang,
                header_text=header_text.strip() or None,
                logo=logo,
            )

            # Wczytaj wynikowy PDF do pobrania
            pdf_bytes = Path(output_path).read_bytes()

        except Exception as e:
            st.error(f"Błąd generowania: {e}")
            st.stop()

    st.success(f"PDF gotowy — zapisany w `output/oferta_katalogowa_3x3.pdf`")
    st.download_button(
        label="Pobierz PDF",
        data=pdf_bytes,
        file_name="oferta_katalogowa_3x3.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

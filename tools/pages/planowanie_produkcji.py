"""
pages/planowanie_produkcji.py — Planowanie produkcji CZNI.

Uruchamiana z menu głównego: streamlit run tools/app.py
"""

import tempfile
from datetime import date
from pathlib import Path
import sys

import streamlit as st

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT))

from tools.lib.pp_demand import fetch_demand
from tools.lib.pp_supply import fetch_supply
from tools.lib.pp_bom import load_bom
from tools.lib.pp_gap import compute_gap
from tools.lib.pp_export import export_plan

_OUTPUT_DIR = _ROOT / "output/planowanie"

st.set_page_config(page_title="Planowanie Produkcji", layout="centered")
st.markdown("<style>.block-container { max-width: 640px; }</style>", unsafe_allow_html=True)

if st.button("← Menu główne"):
    st.switch_page("app.py")

st.markdown(
    "<h2 style='color:#1A1A1A; margin-bottom:4px;'>Planowanie Produkcji "
    "<span style='color:#FAA400'>CZNI</span></h2>",
    unsafe_allow_html=True,
)
st.markdown("<hr style='border:2px solid #FAA400; margin-top:0;'>", unsafe_allow_html=True)

st.info(
    "Generuje Excel z 4 arkuszami: zamówienia CZNI, zapotrzebowanie surowców, "
    "stany OTOR_SUR i gap analysis (braki zaznaczone czerwonym)."
)

# --- Parametry ---
col1, col2 = st.columns([1, 2])
with col1:
    year = st.number_input("Rok realizacji:", min_value=2020, max_value=2035,
                            value=date.today().year, step=1)

st.divider()

st.caption("Plik wyceny BOM (Wycena PQ.xlsm) — arkusz 'Wycena Zniczy'")
uploaded_bom = st.file_uploader("Wybierz plik .xlsm", type=["xlsm", "xlsx"])

st.divider()

xlsx_bytes = None
output_name = f"planowanie_CZNI_{year}_{date.today()}.xlsx"

if st.button("Generuj raport", type="primary", use_container_width=True):
    if not uploaded_bom:
        st.error("Wybierz plik wyceny BOM przed generowaniem.")
        st.stop()

    try:
        with st.spinner(f"Pobieranie zamówień CZNI {year} z ERP…"):
            demand = fetch_demand(int(year))

        if not demand:
            st.warning(f"Brak zamówień niepotwierdzonych CZNI dla roku {year}.")
            st.stop()

        with st.spinner("Wczytywanie BOM z pliku wyceny…"):
            with tempfile.NamedTemporaryFile(suffix=".xlsm", delete=False) as tmp:
                tmp.write(uploaded_bom.read())
                tmp_path = Path(tmp.name)
            bom = load_bom(tmp_path)

        with st.spinner("Pobieranie stanów OTOR_SUR z ERP…"):
            supply = fetch_supply()

        with st.spinner("Obliczanie gap analysis…"):
            gaps, warns = compute_gap(demand, bom, supply)
        for w in warns:
            st.warning(w)

        supply_rows = [
            {"Towar_Kod": k, "Towar_Nazwa": "", "Jednostka": "", "Stan": v}
            for k, v in supply.items()
        ]

        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = _OUTPUT_DIR / output_name
        export_plan(demand, supply, gaps, supply_rows, out_path)
        xlsx_bytes = out_path.read_bytes()

        braki = sum(1 for g in gaps if g.brak > 0)
        st.success(
            f"OK — {len(demand)} pozycji zamówień, "
            f"{len(gaps)} surowców, {braki} z brakiem."
        )

    except RuntimeError as e:
        st.error(str(e))
        st.stop()
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

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
from tools.lib.pp_bom import load_bom, load_efficiency
from tools.lib.pp_capacity import load_capacity
from tools.lib.pp_gap import compute_gap
from tools.lib.pp_export import export_plan
from tools.lib.pp_schedule import build_schedule
from tools.lib.pp_produced import fetch_produced

_OUTPUT_DIR = _ROOT / "output/planowanie"

st.set_page_config(page_title="Planowanie Produkcji", layout="centered")
st.markdown("<style>.block-container { max-width: 680px; }</style>", unsafe_allow_html=True)

if st.button("← Menu główne"):
    st.switch_page("app.py")

st.markdown(
    "<h2 style='color:#1A1A1A; margin-bottom:4px;'>Planowanie Produkcji "
    "<span style='color:#FAA400'>CZNI</span></h2>",
    unsafe_allow_html=True,
)
st.markdown("<hr style='border:2px solid #FAA400; margin-top:0;'>", unsafe_allow_html=True)

# ── Parametry ─────────────────────────────────────────────────────────────────

col1, col2 = st.columns([1, 2])
with col1:
    year = st.number_input("Rok realizacji:", min_value=2020, max_value=2035,
                            value=date.today().year, step=1)

mode = st.radio(
    "Tryb:",
    options=["gap", "schedule", "all"],
    format_func=lambda m: {
        "gap": "Gap Analysis (4 arkusze)",
        "schedule": "Harmonogram Run 1 — bez priorytetów (7 arkuszy)",
        "all": "Harmonogram Run 2 — z priorytetami (7 arkuszy)",
    }[m],
    horizontal=True,
)

st.divider()

# ── Pliki wejściowe ───────────────────────────────────────────────────────────

st.caption("Plik wyceny BOM (Wycena PQ.xlsm) — arkusz 'Wycena Zniczy'")
uploaded_bom = st.file_uploader("Wybierz plik .xlsm / .xlsx", type=["xlsm", "xlsx"],
                                 key="bom")

if mode in ("schedule", "all"):
    st.caption("Plik mocy produkcyjnych (moce produkcyjne.xlsx)")
    uploaded_cap = st.file_uploader("Wybierz plik .xlsx", type=["xlsx"], key="cap")

    start_date = st.date_input("Data startu harmonogramu:", value=date.today())

    if mode == "all":
        st.caption(
            "Plik z priorytetami — Arkusz 5 z poprzedniego runu (Run 1). "
            "Wpisz '1' w kolumnie Priorytet dla wybranych zamówień."
        )
        uploaded_prio = st.file_uploader("Wybierz plik .xlsx z priorytetami",
                                          type=["xlsx"], key="prio")
    else:
        uploaded_prio = None
else:
    uploaded_cap = None
    uploaded_prio = None
    start_date = date.today()

st.divider()

# ── Generowanie ───────────────────────────────────────────────────────────────

xlsx_bytes = None
output_name = f"planowanie_CZNI_{year}_{date.today()}.xlsx"

if st.button("Generuj raport", type="primary", use_container_width=True):
    if not uploaded_bom:
        st.error("Wybierz plik wyceny BOM przed generowaniem.")
        st.stop()
    if mode in ("schedule", "all") and not uploaded_cap:
        st.error("Wybierz plik mocy produkcyjnych.")
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
                bom_path = Path(tmp.name)
            bom = load_bom(bom_path)

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

        schedule = None
        priorities: set[str] = set()

        if mode in ("schedule", "all"):
            with st.spinner("Wczytywanie mocy produkcyjnych…"):
                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                    tmp.write(uploaded_cap.read())
                    cap_path = Path(tmp.name)
                capacity = load_capacity(cap_path)

            with st.spinner("Wczytywanie wydajności z BOM…"):
                efficiency = load_efficiency(bom_path)

            if mode == "all" and uploaded_prio:
                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                    tmp.write(uploaded_prio.read())
                    prio_path = Path(tmp.name)
                priorities = _load_priorities(prio_path)
                st.info(f"Zamówienia z priorytetem: {len(priorities)}")

            with st.spinner("Pobieranie przyjętej produkcji PW Otorowo…"):
                try:
                    produced = fetch_produced(int(year))
                    st.caption(f"Wyprodukowane kody CZNI: {len(produced)}")
                except RuntimeError as e:
                    st.warning(f"Brak danych PW Otorowo: {e} — harmonogram bez odjęcia produkcji.")
                    produced = {}

            with st.spinner("Budowanie harmonogramu (EDF + priorytet)…"):
                schedule = build_schedule(
                    demand, efficiency, produced, capacity, priorities, start_date
                )

        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = _OUTPUT_DIR / output_name
        export_plan(demand, supply, gaps, supply_rows, out_path,
                    schedule=schedule, priorities=priorities, start_date=start_date)
        xlsx_bytes = out_path.read_bytes()

        braki = sum(1 for g in gaps if g.brak > 0)
        msg = (
            f"OK — {len(demand)} pozycji zamówień, "
            f"{len(gaps)} surowców, {braki} z brakiem."
        )
        if schedule is not None:
            msg += f" Slotów harmonogramu: {len(schedule)}."
        st.success(msg)

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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_priorities(prio_path: Path) -> set[str]:
    """Wczytuje Nr_Zamowienia z Priorytet=1 z arkusza xlsx."""
    import warnings
    import openpyxl
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wb = openpyxl.load_workbook(prio_path, read_only=True, data_only=True)
    ws = wb.active
    priorities: set[str] = set()
    header = None
    for row in ws.iter_rows(values_only=True):
        if header is None:
            header = [str(c).strip() if c else "" for c in row]
            continue
        try:
            nr_idx = header.index("Nr_Zamowienia")
            prio_idx = header.index("Priorytet")
        except ValueError:
            break
        nr = row[nr_idx]
        prio = row[prio_idx]
        if nr and str(prio).strip() == "1":
            priorities.add(str(nr))
    wb.close()
    return priorities

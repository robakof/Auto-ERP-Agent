"""
app.py — Menu główne platformy narzędziowej.

Uruchomienie:
    streamlit run tools/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Narzędzia — CEiM",
    page_icon="🧰",
    layout="centered",
)

st.markdown("""
<style>
    .block-container { max-width: 860px; }
    .app-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px 16px;
        text-align: center;
        background: #fafafa;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .app-card.inactive {
        opacity: 0.45;
        pointer-events: none;
    }
    .app-icon { font-size: 2rem; margin-bottom: 6px; }
    .app-name { font-weight: 600; font-size: 0.95rem; color: #1A1A1A; }
    .app-desc { font-size: 0.78rem; color: #6B6B6B; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# --- Nagłówek ---
st.markdown(
    "<h2 style='color:#1A1A1A; margin-bottom:2px;'>Narzędzia "
    "<span style='color:#FAA400'>CEiM</span></h2>",
    unsafe_allow_html=True,
)
st.caption("Wybierz narzędzie poniżej.")
st.markdown("<hr style='border:2px solid #FAA400; margin-top:4px;'>", unsafe_allow_html=True)

# --- Rejestr aplikacji ---
# active: True = karta klikalnoana, False = wkrótce
APPS = [
    {
        "name": "Oferta Katalogowa 3×3",
        "desc": "Generator PDF oferty katalogowej w siatce 3×3",
        "tip": "Excel: kolumny 'Akronim produktu' i 'Cena sprzedaży' w pierwszym wierszu. Wybierz język, logo i nagłówek — kliknij Generuj PDF.",
        "icon": "📄",
        "page": "pages/oferta_katalogowa_3x3.py",
        "active": True,
    },
    {
        "name": "Etykiety Próbek",
        "desc": "Generowanie etykiet próbek ofertowych",
        "tip": "Z ERP: wybierz rok i klienta. Z pliku Excel: kolumna 'Kod' z kodami produktów (pierwszy wiersz = nagłówek). Pobierz Word.",
        "icon": "🏷️",
        "page": "pages/etykiety_wysylkowe.py",
        "active": True,
    },
    {
        "name": "Ofertowanie",
        "desc": "Eksport produktów ERP do Excel ze zdjęciami i parametrami",
        "icon": "📦",
        "page": "pages/ofertowanie.py",
        "active": True,
    },
    {
        "name": "Planowanie Produkcji",
        "desc": "Zamówienia CZNI + BOM + gap analysis surowców",
        "tip": "Wybierz rok realizacji i załaduj plik Wycena PQ.xlsm. Generuje Excel z 4 arkuszami.",
        "icon": "🏭",
        "page": "pages/planowanie_produkcji.py",
        "active": True,
    },
    {
        "name": "Oferta Handlowa Kerti",
        "desc": "Generator PDF oferty szkła Kerti (design katalogowy)",
        "tip": "Excel: kolumna 'Akronim produktu' + opcjonalnie 'Nowość'. Dane z ERP.",
        "icon": "🪟",
        "page": "pages/oferta_handlowa.py",
        "active": True,
    },
    {
        "name": "Preprocessing Zdjęć",
        "desc": "Przygotowanie zdjęć produktowych do katalogu",
        "icon": "🖼️",
        "page": None,
        "active": False,
    },
    {
        "name": "Oferta Katalogowa",
        "desc": "Klasyczny generator PDF oferty katalogowej",
        "icon": "📋",
        "page": None,
        "active": False,
    },
    {
        "name": "— wkrótce —",
        "desc": "",
        "icon": "⬜",
        "page": None,
        "active": False,
    },
    {
        "name": "— wkrótce —",
        "desc": "",
        "icon": "⬜",
        "page": None,
        "active": False,
    },
    {
        "name": "— wkrótce —",
        "desc": "",
        "icon": "⬜",
        "page": None,
        "active": False,
    },
    {
        "name": "— wkrótce —",
        "desc": "",
        "icon": "⬜",
        "page": None,
        "active": False,
    },
]

# --- Siatka 3 kolumny ---
COLS = 3
rows = [APPS[i:i+COLS] for i in range(0, len(APPS), COLS)]

for row in rows:
    cols = st.columns(COLS, gap="medium")
    for col, app in zip(cols, row):
        with col:
            if app["active"] and app["page"]:
                if st.button(
                    f"{app['icon']}\n\n**{app['name']}**\n\n{app['desc']}",
                    key=app["name"],
                    use_container_width=True,
                    help=app["desc"],
                ):
                    st.switch_page(app["page"])
            else:
                st.markdown(
                    f"<div class='app-card inactive'>"
                    f"<div class='app-icon'>{app['icon']}</div>"
                    f"<div class='app-name'>{app['name']}</div>"
                    f"<div class='app-desc'>{app['desc']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

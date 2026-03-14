import sys; sys.path.insert(0, '.')
from tools.lib.agent_bus import AgentBus
bus = AgentBus()

bus.send_message("erp_specialist", "developer", "Znalazlem blad w widoku Rozrachunki — Stan&2 daje zle wyniki dla kont walutowych. Prosze o weryfikacje.")
bus.send_message("analyst", "human", "Proszę o zatwierdzenie raportu jakości danych dla AIBI.KntKarty przed wdrożeniem.", type="flag_human")
bus.add_session_log("developer", "Sesja 2026-03-13: agent_bus faza 1.5 zakonczona. Nowe tabele: suggestions, backlog, session_log. Migracja 34 wpisow. render.py gotowy.")
bus.add_session_log("erp_specialist", "Sesja 2026-03-12: widok Rozrachunki.sql — otwarte: Stan&2 wymaga korekty, priorytet GenDokMag wyzszy.")
print("Gotowe")

import sys; sys.path.insert(0, '.')
from tools.lib.agent_bus import AgentBus
bus = AgentBus()

areas = {
    1: "Dev", 2: "Bot", 3: "Bot", 4: "Bot", 5: "Bot", 6: "Bot",
    7: "Arch", 8: "Arch", 9: "Arch", 10: "Arch", 11: "ERP",
    12: "Arch", 13: "Arch", 14: "Arch", 15: "Arch",
    16: "Metodolog", 17: "Metodolog", 18: "Arch", 23: "Dev",
}

for bid, area in areas.items():
    bus._conn.execute("UPDATE backlog SET area=? WHERE id=?", (area, bid))
bus._conn.commit()
print("Gotowe")

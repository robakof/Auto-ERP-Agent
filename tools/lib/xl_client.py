"""XlClient — Python wrapper dla Comarch XL API przez XlProxy subprocess.

Każda metoda XL API dostępna przez invoke(). Typed helpers dla najczęstszych operacji.
"""

from tools.lib import xl_session


class XlClient:
    # --- generyczny invoke ---

    def invoke(self, method: str, **params) -> dict:
        """Wywołaj dowolną metodę XL API.

        Wersja=20251 ustawiana automatycznie. sesja_id pobierana z singletona.
        Przykład: client.invoke("XLNowyDokument", TrNTyp=524288)
        """
        client, sesja_id = xl_session.get()
        return client.send({
            "cmd":      "invoke",
            "method":   method,
            "sesja_id": sesja_id,
            "params":   {"Wersja": 20251, **params},
        })

    # --- Logowanie (zarządza xl_session) ---

    def logout(self) -> None:
        xl_session.logout()

    # --- Atrybuty ---

    def dodaj_atrybut(self, gid_typ: int, gid_numer: int, gid_firma: int,
                      klasa: str, wartosc: str) -> dict:
        return self.invoke(
            "XLDodajAtrybut",
            GIDTyp=gid_typ, GIDNumer=gid_numer, GIDFirma=gid_firma,
            GIDLp=0, GIDSubLp=0, Klasa=klasa, Wartosc=wartosc,
        )

    # --- Dokumenty handlowe ---

    def nowy_dokument(self, typ_dok: int, **params) -> dict:
        return self.invoke("XLNowyDokument", TrNTyp=typ_dok, **params)

    def dodaj_pozycje(self, **params) -> dict:
        return self.invoke("XLDodajPozycje", **params)

    def zamknij_dokument(self, **params) -> dict:
        return self.invoke("XLZamknijDokument", **params)

    def otworz_dokument(self, **params) -> dict:
        return self.invoke("XLOtworzDokument", **params)

    # --- Zamówienia ---

    def nowy_dokument_zam(self, **params) -> dict:
        return self.invoke("XLNowyDokumentZam", **params)

    def dodaj_pozycje_zam(self, **params) -> dict:
        return self.invoke("XLDodajPozycjeZam", **params)

    def zamknij_dokument_zam(self, **params) -> dict:
        return self.invoke("XLZamknijDokumentZam", **params)

    # --- Kontrahenci ---

    def nowy_kontrahent(self, **params) -> dict:
        return self.invoke("XLNowyKontrahent", **params)

    def zamknij_kontrahenta(self, **params) -> dict:
        return self.invoke("XLZamknijKontrahenta", **params)

    # --- Towary ---

    def nowy_towar(self, **params) -> dict:
        return self.invoke("XLNowyTowar", **params)

    def zamknij_towar(self, **params) -> dict:
        return self.invoke("XLZamknijTowar", **params)

    # --- Transakcje ---

    def transakcja(self, begin: bool) -> dict:
        """begin=True → START TRANSACTION, begin=False → COMMIT."""
        return self.invoke("XLTransakcja", Transakcja=1 if begin else 0)

    # --- Diagnostyka ---

    def opis_bledu(self) -> dict:
        client, _ = xl_session.get()
        return client.send({"cmd": "blad"})

    def pobierz_zdarzenia(self) -> list[dict]:
        """Zwraca listę zdarzeń z kolejki XL API."""
        client, _ = xl_session.get()
        ilosc_resp = client.send({"cmd": "blad"})
        count_resp = self.invoke("XLPobierzIloscZdarzen")
        if not count_resp.get("ok"):
            return []
        count = count_resp.get("data", {}).get("IloscZdarzen", 0)
        return [
            self.invoke("XLPobierzZdarzenie", numer=i)
            for i in range(1, int(count) + 1)
        ]

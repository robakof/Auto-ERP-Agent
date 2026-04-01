"""
Generuje KSeF FA(2) XML dla jednej faktury.
Prototype — dane z CDN.TraNag/TraElem/TraVat/TraPlat/KntKarty/Firma.
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime
from lxml import etree

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from sql_query import run_query

GID_NUMER_DEFAULT = 8981092   # FRA/266 z 2026-03-31

_SQL = """
SELECT
    'FA'                                                        AS KSeF_KodFormularza,
    2                                                           AS KSeF_WariantFormularza,
    f.Frm_NIP                                                   AS P1_NIP,
    RTRIM(f.Frm_Nazwa1) + ' ' + RTRIM(f.Frm_Nazwa2)            AS P1_PelnaNazwa,
    f.Frm_Kraj                                                  AS P1_KodKraju,
    RTRIM(f.Frm_Ulica)                                          AS P1_AdresL1,
    f.Frm_KodP + ' ' + RTRIM(f.Frm_Miasto)                     AS P1_AdresL2,
    RTRIM(k.Knt_Nip)                                            AS P2_NIP,
    CASE WHEN RTRIM(k.Knt_NipPrefiks) = '' THEN 'PL' ELSE RTRIM(k.Knt_NipPrefiks) END AS P2_PrefiksNIP,
    RTRIM(k.Knt_Nazwa1)                                         AS P2_PelnaNazwa,
    k.Knt_Kraj                                                  AS P2_KodKraju,
    RTRIM(k.Knt_Ulica)                                          AS P2_AdresL1,
    k.Knt_KodP + ' ' + RTRIM(k.Knt_Miasto)                     AS P2_AdresL2,
    n.TrN_Waluta                                                AS Fa_KodWaluty,
    CONVERT(DATE, DATEADD(day, n.TrN_Data2, '1800-12-28'))      AS Fa_P1_DataWystawienia,
    CASE WHEN n.TrN_DataSprOrg > 0
         THEN CONVERT(DATE, DATEADD(day, n.TrN_DataSprOrg, '1800-12-28'))
         ELSE CONVERT(DATE, DATEADD(day, n.TrN_Data2, '1800-12-28'))
    END                                                         AS Fa_P2_DataSprzedazy,
    RTRIM(n.TrN_TrNSeria) + '/' + CAST(n.TrN_TrNNumer AS VARCHAR(20)) AS Fa_P2A_NumerFaktury,
    CASE WHEN NULLIF(RTRIM(n.TrN_NrKorekty), '') IS NULL THEN 'VAT' ELSE 'KOR' END AS Fa_RodzajFaktury,
    v23.NettoR                                                  AS Fa_P13_1_Podstawa23,
    v23.VatR                                                    AS Fa_P14_1_VAT23,
    v8.NettoR                                                   AS Fa_P13_2_Podstawa8,
    v8.VatR                                                     AS Fa_P14_2_VAT8,
    v5.NettoR                                                   AS Fa_P13_3_Podstawa5,
    v5.VatR                                                     AS Fa_P14_3_VAT5,
    v0.NettoR                                                   AS Fa_P13_5_Podstawa0,
    v0.VatR                                                     AS Fa_P14_5_VAT0,
    vZW.NettoR                                                  AS Fa_P13_6_PodstawaZW,
    vNP.NettoR                                                  AS Fa_P13_7_PodstawaNP,
    n.TrN_NettoR + n.TrN_VatR                                   AS Fa_P15_KwotaNaleznosci,
    CASE WHEN n.TrN_MPP = 1 THEN '1' ELSE '2' END              AS Fa_P16_MPP,
    e.TrE_GIDLp                                                 AS Wiersz_NrPozycji,
    RTRIM(e.TrE_TwrNazwa)                                       AS Wiersz_P7_NazwaTowaru,
    RTRIM(e.TrE_JmZ)                                            AS Wiersz_P8A_JM,
    e.TrE_Ilosc                                                 AS Wiersz_P8B_Ilosc,
    e.TrE_Cena                                                  AS Wiersz_P9A_CenaNettoJedn,
    e.TrE_KsiegowaNetto                                         AS Wiersz_P10_WartoscNetto,
    CASE e.TrE_GrupaPod
        WHEN 'A' THEN '23' WHEN 'B' THEN '8' WHEN 'C' THEN '5'
        WHEN 'F' THEN '0'  WHEN 'D' THEN 'ZW' WHEN 'E' THEN 'NP'
        ELSE CAST(CAST(e.TrE_StawkaPod AS DECIMAL(5,0)) AS VARCHAR(5))
    END                                                         AS Wiersz_P11_StawkaVAT,
    e.TrE_KsiegowaBrutto - e.TrE_KsiegowaNetto                 AS Wiersz_P12_KwotaVAT,
    CONVERT(DATE, DATEADD(day, p.TrP_Termin, '1800-12-28'))     AS Plat_TerminPlatnosci,
    CASE p.TrP_FormaNr WHEN 10 THEN '1' WHEN 20 THEN '6' WHEN 50 THEN '3'
        ELSE CAST(p.TrP_FormaNr AS VARCHAR(5)) END              AS Plat_KodFormyPlatnosci,
    CASE WHEN p.TrP_FormaNr = 20 THEN rb.RkB_NrRachunku ELSE NULL END AS Plat_NrRachunkuBankowego

FROM CDN.TraNag n
CROSS JOIN (SELECT TOP 1 Frm_NIP, Frm_Nazwa1, Frm_Nazwa2,
    Frm_Kraj, Frm_Ulica, Frm_KodP, Frm_Miasto FROM CDN.Firma) f
JOIN CDN.KntKarty k ON k.Knt_GIDNumer = n.TrN_KntNumer AND k.Knt_GIDTyp = 32
JOIN CDN.TraElem e ON e.TrE_GIDTyp = n.TrN_GIDTyp AND e.TrE_GIDNumer = n.TrN_GIDNumer
LEFT JOIN (SELECT TrV_GIDTyp, TrV_GIDNumer, SUM(TrV_NettoR) AS NettoR, SUM(TrV_VatR) AS VatR
    FROM CDN.TraVat WHERE TrV_FlagaVat=1 AND TrV_StawkaPod='23.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer) v23 ON v23.TrV_GIDTyp=n.TrN_GIDTyp AND v23.TrV_GIDNumer=n.TrN_GIDNumer
LEFT JOIN (SELECT TrV_GIDTyp, TrV_GIDNumer, SUM(TrV_NettoR) AS NettoR, SUM(TrV_VatR) AS VatR
    FROM CDN.TraVat WHERE TrV_FlagaVat=1 AND TrV_StawkaPod='8.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer) v8 ON v8.TrV_GIDTyp=n.TrN_GIDTyp AND v8.TrV_GIDNumer=n.TrN_GIDNumer
LEFT JOIN (SELECT TrV_GIDTyp, TrV_GIDNumer, SUM(TrV_NettoR) AS NettoR, SUM(TrV_VatR) AS VatR
    FROM CDN.TraVat WHERE TrV_FlagaVat=1 AND TrV_StawkaPod='5.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer) v5 ON v5.TrV_GIDTyp=n.TrN_GIDTyp AND v5.TrV_GIDNumer=n.TrN_GIDNumer
LEFT JOIN (SELECT TrV_GIDTyp, TrV_GIDNumer, SUM(TrV_NettoR) AS NettoR, SUM(TrV_VatR) AS VatR
    FROM CDN.TraVat WHERE TrV_FlagaVat=1 AND TrV_StawkaPod='0.00'
    GROUP BY TrV_GIDTyp, TrV_GIDNumer) v0 ON v0.TrV_GIDTyp=n.TrN_GIDTyp AND v0.TrV_GIDNumer=n.TrN_GIDNumer
LEFT JOIN (SELECT TrV_GIDTyp, TrV_GIDNumer, SUM(TrV_NettoR) AS NettoR
    FROM CDN.TraVat WHERE TrV_FlagaVat=2
    GROUP BY TrV_GIDTyp, TrV_GIDNumer) vZW ON vZW.TrV_GIDTyp=n.TrN_GIDTyp AND vZW.TrV_GIDNumer=n.TrN_GIDNumer
LEFT JOIN (SELECT TrV_GIDTyp, TrV_GIDNumer, SUM(TrV_NettoR) AS NettoR
    FROM CDN.TraVat WHERE TrV_FlagaVat=0
    GROUP BY TrV_GIDTyp, TrV_GIDNumer) vNP ON vNP.TrV_GIDTyp=n.TrN_GIDTyp AND vNP.TrV_GIDNumer=n.TrN_GIDNumer
LEFT JOIN (SELECT TrP_GIDTyp, TrP_GIDNumer, TrP_Termin, TrP_FormaNr, TrP_FormaNazwa, TrP_RachBank,
    ROW_NUMBER() OVER (PARTITION BY TrP_GIDTyp, TrP_GIDNumer ORDER BY TrP_GIDLp) AS rn
    FROM CDN.TraPlat) p ON p.TrP_GIDTyp=n.TrN_GIDTyp AND p.TrP_GIDNumer=n.TrN_GIDNumer AND p.rn=1
LEFT JOIN CDN.RachunkiBankowe rb ON rb.RkB_Id=p.TrP_RachBank AND p.TrP_FormaNr=20
WHERE n.TrN_GIDTyp = 2033 AND n.TrN_GIDNumer = {gid_numer}
ORDER BY e.TrE_GIDLp
"""

NS = "http://crd.gov.pl/wzor/2025/06/25/13775/"
NSMAP = {None: NS}


def E(parent, tag, text=None, **attrib):
    """Tworzy element w przestrzeni nazw KSeF i opcjonalnie ustawia text."""
    el = etree.SubElement(parent, f"{{{NS}}}{tag}", **attrib)
    if text is not None:
        el.text = text
    return el


def v(row, col):
    val = row.get(col)
    if val is None:
        return None
    return str(val).strip()


def fmt_decimal(val, places=2):
    if val is None:
        return None
    try:
        return f"{float(val):.{places}f}"
    except Exception:
        return str(val)


def build_xml(rows):
    r = rows[0]

    root = etree.Element(f"{{{NS}}}Faktura", nsmap=NSMAP)

    # Naglowek
    nag = E(root, "Naglowek")
    kf = E(nag, "KodFormularza", text="FA",
           kodSystemowy="FA (3)", wersjaSchemy="1-0E")
    E(nag, "WariantFormularza", text="3")
    E(nag, "DataWytworzeniaFa", text=datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "Z")
    E(nag, "SystemInfo", text="Comarch ERP XL")

    # Podmiot1
    p1 = E(root, "Podmiot1")
    di1 = E(p1, "DaneIdentyfikacyjne")
    E(di1, "NIP", text=v(r, "P1_NIP"))
    E(di1, "Nazwa", text=v(r, "P1_PelnaNazwa"))
    adr1 = E(p1, "Adres")
    E(adr1, "KodKraju", text=v(r, "P1_KodKraju"))
    E(adr1, "AdresL1", text=v(r, "P1_AdresL1"))
    E(adr1, "AdresL2", text=v(r, "P1_AdresL2"))

    # Podmiot2
    p2 = E(root, "Podmiot2")
    di2 = E(p2, "DaneIdentyfikacyjne")
    E(di2, "NIP", text=v(r, "P2_NIP"))
    E(di2, "Nazwa", text=v(r, "P2_PelnaNazwa"))
    adr2 = E(p2, "Adres")
    E(adr2, "KodKraju", text=v(r, "P2_KodKraju"))
    E(adr2, "AdresL1", text=v(r, "P2_AdresL1"))
    E(adr2, "AdresL2", text=v(r, "P2_AdresL2"))
    E(p2, "JST", text="2")
    E(p2, "GV", text="2")

    # Fa
    fa = E(root, "Fa")
    E(fa, "KodWaluty", text=v(r, "Fa_KodWaluty"))
    E(fa, "P_1", text=v(r, "Fa_P1_DataWystawienia"))
    E(fa, "P_2", text=v(r, "Fa_P2A_NumerFaktury"))

    # P_6 = data dokonania dostawy (tylko gdy inna niż data wystawienia)
    data_spr = v(r, "Fa_P2_DataSprzedazy")
    data_wyst = v(r, "Fa_P1_DataWystawienia")
    if data_spr and data_spr != data_wyst:
        E(fa, "P_6", text=data_spr)

    # VAT per stawka
    p13_map = [
        ("Fa_P13_1_Podstawa23", "Fa_P14_1_VAT23", "P_13_1", "P_14_1"),
        ("Fa_P13_2_Podstawa8",  "Fa_P14_2_VAT8",  "P_13_2", "P_14_2"),
        ("Fa_P13_3_Podstawa5",  "Fa_P14_3_VAT5",  "P_13_3", "P_14_3"),
        ("Fa_P13_5_Podstawa0",  "Fa_P14_5_VAT0",  "P_13_5", "P_14_5"),
    ]
    for netto_col, vat_col, netto_tag, vat_tag in p13_map:
        netto = r.get(netto_col)
        vat   = r.get(vat_col)
        if netto is not None:
            E(fa, netto_tag, text=fmt_decimal(netto))
            E(fa, vat_tag,   text=fmt_decimal(vat))

    if r.get("Fa_P13_6_PodstawaZW") is not None:
        E(fa, "P_13_6", text=fmt_decimal(r["Fa_P13_6_PodstawaZW"]))
    if r.get("Fa_P13_7_PodstawaNP") is not None:
        E(fa, "P_13_7", text=fmt_decimal(r["Fa_P13_7_PodstawaNP"]))

    E(fa, "P_15", text=fmt_decimal(r.get("Fa_P15_KwotaNaleznosci")))

    # Adnotacje
    adt = E(fa, "Adnotacje")
    E(adt, "P_16",  text=v(r, "Fa_P16_MPP"))
    E(adt, "P_17",  text="2")
    E(adt, "P_18",  text="2")
    E(adt, "P_18A", text="2")
    zwol = E(adt, "Zwolnienie")
    E(zwol, "P_19N", text="1")
    nst = E(adt, "NoweSrodkiTransportu")
    E(nst, "P_22N", text="1")
    E(adt, "P_23", text="2")
    pmar = E(adt, "PMarzy")
    E(pmar, "P_PMarzyN", text="1")

    E(fa, "RodzajFaktury", text=v(r, "Fa_RodzajFaktury"))

    # FaWiersz — pozycje
    for row in rows:
        fw = E(fa, "FaWiersz")
        E(fw, "NrWierszaFa", text=str(row.get("Wiersz_NrPozycji", "")))
        E(fw, "P_7",  text=v(row, "Wiersz_P7_NazwaTowaru"))
        E(fw, "P_8A", text=v(row, "Wiersz_P8A_JM"))
        ilosc = fmt_decimal(row.get("Wiersz_P8B_Ilosc"), 4)
        if ilosc:
            ilosc = ilosc.rstrip("0").rstrip(".")
        E(fw, "P_8B",  text=ilosc)
        E(fw, "P_9A",  text=fmt_decimal(row.get("Wiersz_P9A_CenaNettoJedn")))
        # P_10 = rabat/opust — pomijamy (brak osobnej kolumny rabatu)
        E(fw, "P_11",  text=fmt_decimal(row.get("Wiersz_P10_WartoscNetto")))  # wartość netto
        E(fw, "P_12",  text=v(row, "Wiersz_P11_StawkaVAT"))                   # stawka VAT (enum)

    # Platnosc
    plat = E(fa, "Platnosc")
    termin_el = E(plat, "TerminPlatnosci")
    E(termin_el, "Termin", text=v(r, "Plat_TerminPlatnosci"))
    E(plat, "FormaPlatnosci", text=v(r, "Plat_KodFormyPlatnosci"))
    rachunek = v(r, "Plat_NrRachunkuBankowego")
    if rachunek:
        E(plat, "Rachunek", text=rachunek)

    return root


def main():
    parser = argparse.ArgumentParser(description="Generuje KSeF XML dla faktury FS.")
    parser.add_argument("--gid", type=int, default=GID_NUMER_DEFAULT, help="TrN_GIDNumer faktury")
    args = parser.parse_args()

    sql = _SQL.format(gid_numer=args.gid)
    res = run_query(sql, inject_top=None)
    if not res["ok"]:
        print("ERROR SQL:", res["error"]["message"])
        sys.exit(1)

    cols = res["data"]["columns"]
    rows = [dict(zip(cols, row)) for row in res["data"]["rows"]]
    print(f"Pobrano {len(rows)} pozycji faktury.")

    root = build_xml(rows)

    xml_bytes = etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
    )

    out_dir = Path(__file__).parent.parent / "output" / "ksef"
    out_dir.mkdir(parents=True, exist_ok=True)

    nr = rows[0].get("Fa_P2A_NumerFaktury", "faktura")
    nr = str(nr).replace("/", "_")
    data = str(rows[0].get("Fa_P1_DataWystawienia", ""))[:10]
    out_path = out_dir / f"ksef_{nr}_{data}.xml"

    out_path.write_bytes(xml_bytes)
    print(f"XML zapisany: {out_path}")


if __name__ == "__main__":
    main()

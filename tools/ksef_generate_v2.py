"""
Generuje KSeF FA(2) XML z danych ERP XL.

CLI:
    py tools/ksef_generate_v2.py --gid 8981092              # jedna faktura
    py tools/ksef_generate_v2.py --gid 8981092 8981093      # kilka faktur
    py tools/ksef_generate_v2.py --date-from 2026-03-01 --date-to 2026-03-31
    py tools/ksef_generate_v2.py --date-from 2026-03-31     # jeden dzień
    py tools/ksef_generate_v2.py --validate output/schemat.xsd --gid 8981092

Opcje:
    --gid N [N ...]       GID_NUMER faktur(y)
    --date-from YYYY-MM-DD  data wystawienia od
    --date-to YYYY-MM-DD    data wystawienia do (domyślnie = date-from)
    --validate XSD_PATH   walidacja każdego XML przeciw XSD
    --dry-run             pokaż SQL bez wykonania
"""
import argparse
import sys
from itertools import groupby
from operator import itemgetter
from pathlib import Path
from datetime import datetime
from lxml import etree

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

SQL_PATH = Path(__file__).parent.parent / "solutions" / "ksef" / "ksef_fs_draft_v2.sql"
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "ksef"

NS = "http://crd.gov.pl/wzor/2025/06/25/13775/"
NSMAP = {None: NS}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def E(parent, tag, text=None, **attrib):
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


# ---------------------------------------------------------------------------
# SQL builder
# ---------------------------------------------------------------------------

def load_base_sql():
    return SQL_PATH.read_text(encoding="utf-8")


def build_sql(gids=None, date_from=None, date_to=None):
    base = load_base_sql()

    conditions = []
    if gids:
        id_list = ", ".join(str(int(g)) for g in gids)
        conditions.append(f"n.TrN_GIDNumer IN ({id_list})")
    if date_from:
        conditions.append(
            f"DATEADD(day, n.TrN_Data2, '1800-12-28') >= '{date_from}'"
        )
    if date_to:
        conditions.append(
            f"DATEADD(day, n.TrN_Data2, '1800-12-28') <= '{date_to}'"
        )

    if conditions:
        extra = " AND " + " AND ".join(conditions)
        base = base.replace(
            "WHERE n.TrN_GIDTyp = 2033",
            "WHERE n.TrN_GIDTyp = 2033" + extra,
        )

    return base


# ---------------------------------------------------------------------------
# XML builder
# ---------------------------------------------------------------------------

def build_xml(rows):
    r = rows[0]

    root = etree.Element(f"{{{NS}}}Faktura", nsmap=NSMAP)

    # Naglowek
    nag = E(root, "Naglowek")
    E(nag, "KodFormularza", text="FA",
      kodSystemowy="FA (3)", wersjaSchemy="1-0E")
    E(nag, "WariantFormularza", text="3")
    E(nag, "DataWytworzeniaFa",
      text=datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "Z")
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
    adres_l2 = v(r, "P2_AdresL2")
    if adres_l2:
        E(adr2, "AdresL2", text=adres_l2)
    E(p2, "JST", text="2")
    E(p2, "GV", text="2")

    # Fa
    fa = E(root, "Fa")
    E(fa, "KodWaluty", text=v(r, "Fa_KodWaluty"))
    E(fa, "P_1", text=v(r, "Fa_P1_DataWystawienia"))
    E(fa, "P_2", text=v(r, "Fa_P2A_NumerFaktury"))

    data_spr = v(r, "Fa_P2_DataSprzedazy")
    data_wyst = v(r, "Fa_P1_DataWystawienia")
    if data_spr and data_spr != data_wyst:
        E(fa, "P_6", text=data_spr)

    # VAT per stawka
    vat_map = [
        ("Fa_P13_1_Podstawa23", "Fa_P14_1_VAT23", "P_13_1", "P_14_1"),
        ("Fa_P13_2_Podstawa8",  "Fa_P14_2_VAT8",  "P_13_2", "P_14_2"),
        ("Fa_P13_3_Podstawa5",  "Fa_P14_3_VAT5",  "P_13_3", "P_14_3"),
        ("Fa_P13_5_Podstawa0",  "Fa_P14_5_VAT0",  "P_13_5", "P_14_5"),
    ]
    for netto_col, vat_col, netto_tag, vat_tag in vat_map:
        netto = r.get(netto_col)
        vat = r.get(vat_col)
        if netto is not None:
            E(fa, netto_tag, text=fmt_decimal(netto))
            E(fa, vat_tag, text=fmt_decimal(vat))

    if r.get("Fa_P13_6_PodstawaZW") is not None:
        E(fa, "P_13_6", text=fmt_decimal(r["Fa_P13_6_PodstawaZW"]))
    if r.get("Fa_P13_7_PodstawaNP") is not None:
        E(fa, "P_13_7", text=fmt_decimal(r["Fa_P13_7_PodstawaNP"]))

    E(fa, "P_15", text=fmt_decimal(r.get("Fa_P15_KwotaNaleznosci")))

    # Adnotacje
    adt = E(fa, "Adnotacje")
    E(adt, "P_16", text=v(r, "Fa_P16_MPP"))
    E(adt, "P_17", text="2")
    E(adt, "P_18", text="2")
    E(adt, "P_18A", text="2")
    zwol = E(adt, "Zwolnienie")
    E(zwol, "P_19N", text="1")
    nst = E(adt, "NoweSrodkiTransportu")
    E(nst, "P_22N", text="1")
    E(adt, "P_23", text="2")
    pmar = E(adt, "PMarzy")
    E(pmar, "P_PMarzyN", text="1")

    E(fa, "RodzajFaktury", text=v(r, "Fa_RodzajFaktury"))

    # FaWiersz
    for row in rows:
        fw = E(fa, "FaWiersz")
        E(fw, "NrWierszaFa", text=str(row.get("Wiersz_NrPozycji", "")))
        E(fw, "P_7", text=v(row, "Wiersz_P7_NazwaTowaru"))
        gtin = v(row, "Wiersz_GTIN")
        if gtin:
            E(fw, "Indeks", text=gtin)
            E(fw, "GTIN", text=gtin)
        E(fw, "P_8A", text=v(row, "Wiersz_P8A_JM"))
        ilosc = fmt_decimal(row.get("Wiersz_P8B_Ilosc"), 4)
        if ilosc:
            ilosc = ilosc.rstrip("0").rstrip(".")
        E(fw, "P_8B", text=ilosc)
        E(fw, "P_9A", text=fmt_decimal(row.get("Wiersz_P9A_CenaNettoJedn")))
        E(fw, "P_11", text=fmt_decimal(row.get("Wiersz_P10_WartoscNetto")))
        E(fw, "P_12", text=v(row, "Wiersz_P11_StawkaVAT"))

    # Platnosc
    plat = E(fa, "Platnosc")
    termin_el = E(plat, "TerminPlatnosci")
    E(termin_el, "Termin", text=v(r, "Plat_TerminPlatnosci"))
    E(plat, "FormaPlatnosci", text=v(r, "Plat_KodFormyPlatnosci"))
    rachunek = v(r, "Plat_NrRachunkuBankowego")
    if rachunek:
        rb = E(plat, "RachunekBankowy")
        E(rb, "NrRB", text=rachunek)

    return root


# ---------------------------------------------------------------------------
# XSD validation
# ---------------------------------------------------------------------------

def validate_xsd(xml_path, xsd_path):
    with open(xsd_path, "rb") as f:
        schema = etree.XMLSchema(etree.parse(f))
    with open(xml_path, "rb") as f:
        doc = etree.parse(f)

    if schema.validate(doc):
        return True, []

    errors = []
    for err in schema.error_log:
        errors.append(f"Linia {err.line}: {err.message}")
    return False, errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Generuj KSeF FA(2) XML z ERP XL"
    )
    p.add_argument("--gid", type=int, nargs="+",
                    help="GID_NUMER faktur(y)")
    p.add_argument("--date-from", dest="date_from",
                    help="Data wystawienia od (YYYY-MM-DD)")
    p.add_argument("--date-to", dest="date_to",
                    help="Data wystawienia do (YYYY-MM-DD, domyslnie=date-from)")
    p.add_argument("--validate", metavar="XSD_PATH",
                    help="Sciezka do pliku XSD do walidacji")
    p.add_argument("--dry-run", action="store_true",
                    help="Pokaz SQL bez wykonania")
    p.add_argument("--output-dir", dest="output_dir", metavar="KATALOG",
                    help="Katalog wyjsciowy dla plikow XML (domyslnie: output/ksef)")
    return p.parse_args()


def main():
    args = parse_args()

    if not args.gid and not args.date_from:
        print("Podaj --gid N lub --date-from YYYY-MM-DD")
        sys.exit(1)

    date_to = args.date_to or args.date_from

    sql = build_sql(
        gids=args.gid,
        date_from=args.date_from,
        date_to=date_to,
    )

    if args.dry_run:
        print(sql)
        return

    from sql_query import run_query
    res = run_query(sql, inject_top=None)
    if not res["ok"]:
        print("ERROR SQL:", res["error"]["message"])
        sys.exit(1)

    cols = res["data"]["columns"]
    all_rows = [dict(zip(cols, row)) for row in res["data"]["rows"]]

    if not all_rows:
        print("Brak faktur dla podanych kryteriów.")
        sys.exit(0)

    # Grupuj po GIDNumer
    all_rows.sort(key=itemgetter("_GIDNumer"))
    groups = groupby(all_rows, key=itemgetter("_GIDNumer"))

    out_dir = Path(args.output_dir) if args.output_dir else OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    generated = []
    errors = []

    for gid_numer, rows_iter in groups:
        rows = list(rows_iter)
        nr = str(rows[0].get("Fa_P2A_NumerFaktury", "faktura")).replace("/", "_")
        data = str(rows[0].get("Fa_P1_DataWystawienia", ""))[:10]

        root = build_xml(rows)
        xml_bytes = etree.tostring(
            root, xml_declaration=True, encoding="UTF-8", pretty_print=True,
        )

        out_path = out_dir / f"ksef_{nr}_{data}.xml"
        out_path.write_bytes(xml_bytes)
        print(f"  [OK] {nr} ({len(rows)} poz.) -> {out_path.name}")

        # Walidacja XSD
        if args.validate:
            xsd = Path(args.validate)
            if not xsd.exists():
                print(f"  [!] XSD nie istnieje: {xsd}")
            else:
                valid, errs = validate_xsd(out_path, xsd)
                if valid:
                    print(f"  [XSD OK] {out_path.name}")
                else:
                    print(f"  [XSD FAIL] {out_path.name} — {len(errs)} bledow:")
                    for e in errs[:5]:
                        print(f"    {e}")
                    errors.append((nr, errs))

        generated.append(out_path)

    print(f"\nWygenerowano {len(generated)} faktur(y) w {out_dir}")
    if errors:
        print(f"Walidacja XSD: {len(errors)} z bledami.")
        sys.exit(2)


if __name__ == "__main__":
    main()

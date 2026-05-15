"""Load product and package data from mock JSON or ERP export."""

import json
from pathlib import Path


def load_mock_data(products_path: str, packages_path: str) -> tuple[list, list]:
    products = json.loads(Path(products_path).read_text(encoding="utf-8"))
    packages = json.loads(Path(packages_path).read_text(encoding="utf-8"))
    return products, packages


def _filter_packages(raw_packages: list, filt: dict) -> list:
    year = filt.get("year", "")
    exclude = filt.get("exclude_prefixes", [])
    include = filt.get("include_prefixes", [])
    result = []
    for p in raw_packages:
        code = p.get("pakiet_kod", "")
        if year and year not in code:
            continue
        if include and not any(code.startswith(inc) for inc in include):
            continue
        if any(code.startswith(ex) for ex in exclude):
            continue
        result.append(p)
    return result


def _map_product(raw: dict) -> dict:
    return {
        "code_xl": raw.get("KodXL", ""),
        "ean": raw.get("KodEAN", ""),
        "name": raw.get("NazwaHandlowa", ""),
        "price_net": raw.get("CenaNetto", 0),
        "burn_hours": raw.get("CzasPalenia_h"),
        "wax_weight_g": raw.get("GramaturaWkladu_g"),
        "height_net_cm": raw.get("WysokoscNetto_cm"),
        "width_net_cm": raw.get("SzerokoscNetto_cm"),
        "width_gross_cm": raw.get("SzerokoscBrutto_cm"),
        "height_gross_cm": raw.get("WysokoscBrutto_cm"),
        "depth_gross_cm": raw.get("GlebokoscBrutto_cm"),
        "per_pack": raw.get("SztWOpakowaniu"),
        "per_layer": raw.get("SztNaWarstwie"),
        "per_pallet": raw.get("SztNaPalecie"),
        "color": raw.get("Kolor"),
        "season": raw.get("Sezon"),
        "material": raw.get("Material"),
        "scent": raw.get("Zapach"),
        "diameter_cm": raw.get("SrednicaProduktu_cm"),
        "weight_g": raw.get("WagaProduktu_g"),
        "hole_diameter_cm": raw.get("SrednicaOtworu_cm"),
        "group_path": raw.get("GrupaSciezka", ""),
        "default_group": raw.get("GrupaDomyslna"),
        "default_group_parent": raw.get("GrupaDomyslnaParent"),
    }


def _map_package(raw: dict, product_lookup: dict) -> dict:
    items = []
    for s in raw.get("skladniki", []):
        prod = product_lookup.get(s["kod"], {})
        items.append({
            "product_code": s["kod"],
            "product_name": s.get("nazwa", prod.get("name", "")),
            "quantity": s.get("ilosc_szt"),
            "unit_price": prod.get("price_net", 0),
        })
    return {
        "name": raw.get("pakiet_nazwa", ""),
        "code_xl": raw.get("pakiet_kod", ""),
        "items": items,
    }


def load_erp_data(
    products_path: str, packages_path: str, package_filter: dict | None = None,
) -> tuple[list, list]:
    """Load ERP export (Arek format) and map to catalog model."""
    raw_prods = json.loads(Path(products_path).read_text(encoding="utf-8"))
    raw_pkgs = json.loads(Path(packages_path).read_text(encoding="utf-8"))

    products_list = raw_prods.get("products", raw_prods) if isinstance(raw_prods, dict) else raw_prods
    packages_list = raw_pkgs.get("packages", raw_pkgs) if isinstance(raw_pkgs, dict) else raw_pkgs

    if package_filter:
        packages_list = _filter_packages(packages_list, package_filter)

    product_lookup = {p.get("KodXL", ""): _map_product(p) for p in products_list}
    pkg_codes_in_use = set()
    for pkg in packages_list:
        for s in pkg.get("skladniki", []):
            pkg_codes_in_use.add(s["kod"])

    products = [_map_product(p) for p in products_list]
    for p in products:
        p["in_package"] = p["code_xl"] in pkg_codes_in_use
        p["package_name"] = ""
    for pkg in packages_list:
        for s in pkg.get("skladniki", []):
            for p in products:
                if p["code_xl"] == s["kod"]:
                    p["package_name"] = pkg.get("pakiet_nazwa", "")

    packages = [_map_package(pkg, product_lookup) for pkg in packages_list]
    return products, packages


def group_by_package(products: list) -> dict[str, list]:
    groups: dict[str, list] = {}
    for p in products:
        pkg = p.get("package_name", "INNE")
        groups.setdefault(pkg, []).append(p)
    return groups


# --- Standalone product grouping by ERP default group ---
GROUP_DISPLAY_NAMES = {
    "1_PARAFINOWE": "Wkłady",
    "2_OLEJOWE": "Wkłady",
    "3_EKONOMICZNE": "Wkłady",
    "4_ROZSUWANE": "Wkłady",
    "5_SKŁADAKI": "Wkłady",
    "7_OTWARTE": "Wkłady",
    "8_INNE": "Wkłady",
    "6_LEDOWE": "Wkłady LED",
    "7_LEDOWE": "Znicze LED",
    "8_SOLARNE": "Znicze Solarne",
    "3_LAMPIONY": "Lampiony",
    "BEZ WKŁADU": "Lampiony",
    "BEZ WKLADU": "Lampiony",
    "NAFTOWE": "Nowość! Seria Luminox",
    "ALAS0018": "Zapalarki",
    "9_ŚWIECE LED": "Świece LED",
    "10_FIGURKI LED": "Figurki LED",
}

# Groups that change meaning based on parent SUB_CAT
# key: (grp_kod, parent_id) -> display name
# 185 = 3_LAMPIONY, 10 = 1_ZNICZE
GROUP_PARENT_OVERRIDES = {
    ("LEDOWE", 185): "Lampiony",
    ("LEDOWE", 10): "Znicze LED",
}
STANDALONE_GROUP_ORDER = [
    "Lampiony", "Znicze LED", "Znicze Solarne",
    "Wkłady LED", "Świece LED", "Figurki LED", "Zapalarki",
]


def standalone_group_name(default_group: str | None, product_name: str = "",
                          parent_id: int | None = None) -> str:
    # Check parent-specific override first (e.g. LEDOWE under Lampiony vs Znicze)
    if default_group and parent_id is not None:
        key = (default_group, parent_id)
        if key in GROUP_PARENT_OVERRIDES:
            return GROUP_PARENT_OVERRIDES[key]
    if default_group and default_group in GROUP_DISPLAY_NAMES:
        return GROUP_DISPLAY_NAMES[default_group]
    # Fallback: check product name for zapalarki/zapałki
    n = (product_name or "").upper()
    if "ZAPAL" in n or "ZAPAŁ" in n:
        return "Zapalarki"
    return "Wkłady LED"


def category_for_package(pkg_name: str) -> str:
    n = pkg_name.upper()
    if "MAŁ" in n or "MALE" in n:
        return "male"
    if "ŚRED" in n or "SRED" in n:
        return "srednie"
    if "DUŻ" in n or "DUZE" in n:
        return "duze"
    if "LAMP" in n:
        return "lampiony"
    if "WKŁ" in n or "WKLAD" in n:
        return "wklady"
    if "LED" in n:
        return "led"
    if "SOLAR" in n:
        return "solar"
    if "ZAPAL" in n:
        return "zapalarki"
    return "inne"

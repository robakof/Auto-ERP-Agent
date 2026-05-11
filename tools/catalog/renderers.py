"""Catalog renderers — HTML (Jinja2) and Excel (xlsxwriter)."""

import json
from pathlib import Path

import xlsxwriter
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _add_category(products: list, category_fn) -> list:
    for i, p in enumerate(products):
        p["_idx"] = i
        p["_category"] = category_fn(p.get("package_name", ""))
    return products


def render_html(products: list, packages: list, config: dict,
                category_fn) -> str:
    products = _add_category(products, category_fn)
    brandbook = config.get("brandbook", {})
    colors = brandbook.get("colors", {})
    fonts = brandbook.get("fonts", {})
    cat_order = config.get("categories_order", [])
    cat_labels = config.get("category_labels", {})

    css_template = TEMPLATES_DIR / "catalog.css"
    css_content = css_template.read_text(encoding="utf-8")
    env_css = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    css_rendered = env_css.from_string(css_content).render(
        colors=colors, fonts=fonts
    )

    js_content = (TEMPLATES_DIR / "catalog.js").read_text(encoding="utf-8")

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
    )
    template = env.get_template("catalog.html.j2")

    html = template.render(
        catalog_name=config.get("catalog", {}).get("name", "Katalog"),
        client=config.get("catalog", {}).get("client", ""),
        colors=colors,
        fonts=fonts,
        categories_order=cat_order,
        category_labels=cat_labels,
        products_json=json.dumps(products, ensure_ascii=False),
        packages_json=json.dumps(packages, ensure_ascii=False),
        categories_order_json=json.dumps(cat_order, ensure_ascii=False),
        category_labels_json=json.dumps(cat_labels, ensure_ascii=False),
        css=css_rendered,
        js=js_content,
    )
    return html


def write_html(html: str, output_path: str) -> str:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return str(out.resolve())


# ---------------------------------------------------------------------------
# Excel renderer v4 — config-driven, sorted, branded
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_IMAGES_DIR = _PROJECT_ROOT / "assets" / "catalog" / "images"


def _img_scale(img_path: str, tw: int, th: int) -> tuple[float, float]:
    from PIL import Image
    with Image.open(img_path) as im:
        w, h = im.size
    s = min(tw / w, th / h)
    return s, s


def _find_product_image(ean: str) -> str | None:
    if not ean:
        return None
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = _IMAGES_DIR / f"{ean}.{ext}"
        if p.exists():
            return str(p)
    return None


def _excel_cfg(config: dict) -> dict:
    ec = config.get("excel", {})
    return {
        "font": ec.get("font", "Calibri"),
        "photo_h": ec.get("photo_row_height", 90),
        "pkg_h": ec.get("package_row_height", 32),
        "columns": ec.get("columns", []),
        "sort_order": ec.get("package_sort_order", []),
        "sort_products": ec.get("sort_products_by", "price_asc"),
        "section_order": ec.get("section_order"),
    }


def _sort_packages(packages: list, sort_order: list) -> list:
    def _pkg_key(pkg: dict) -> tuple:
        name = (pkg.get("name") or "").upper()
        for i, prefix in enumerate(sort_order):
            if prefix.upper() in name:
                return (i,)
        return (len(sort_order),)
    return sorted(packages, key=_pkg_key)


def _sort_items(items: list, mode: str, prod_lookup: dict) -> list:
    if mode == "price_asc":
        return sorted(items, key=lambda it: it.get("unit_price") or
                       prod_lookup.get(it.get("product_code", ""), {}).get("price_net", 0))
    return items


def _xl_formats(wb: xlsxwriter.Workbook, config: dict) -> dict:
    c = config.get("brandbook", {}).get("colors", {})
    gold = c.get("gold", "#FABC61")
    black = c.get("black", "#000000")
    beige = c.get("beige", "#FDF8F1")
    white = c.get("white", "#FFFFFF")
    dark = c.get("dark_brown", "#2B110C")
    font = _excel_cfg(config)["font"]
    bdr = {"border": 1, "border_color": "#D0D0D0"}
    bd = {"font_name": font, "font_size": 10}
    bdb = {**bd, "bold": True, "font_size": 11}

    def _f(**kw):
        return wb.add_format({**bd, **bdr, "valign": "vcenter", "bg_color": white, **kw})

    def _fb(**kw):
        return wb.add_format({**bdb, **bdr, "valign": "vcenter", "bg_color": white, **kw})

    return {
        "top_bar": wb.add_format({
            **bd, "font_size": 12, "bg_color": beige,
            "font_color": dark, "align": "center", "valign": "vcenter", "border": 0,
        }),
        "top_val": wb.add_format({
            **bd, "bold": True, "font_size": 14, "bg_color": beige,
            "font_color": dark, "num_format": '#,##0.00 "zł"',
            "align": "right", "valign": "vcenter", "border": 0,
        }),
        "header": wb.add_format({
            **bd, "bold": True, "font_size": 9, "align": "center",
            "bg_color": dark, "font_color": white, "text_wrap": True,
            **bdr, "bottom": 2,
        }),
        "pkg_bar": wb.add_format({
            **bd, "bold": True, "font_size": 12, "bg_color": dark,
            "font_color": gold, "align": "center", "valign": "vcenter", **bdr,
        }),
        "pkg_label": wb.add_format({
            **bd, "bold": True, "font_size": 10, "bg_color": dark,
            "font_color": white, "align": "center", "valign": "vcenter", **bdr,
        }),
        "pkg_qty": wb.add_format({
            **bd, "bold": True, "font_size": 12, "bg_color": white,
            "font_color": dark, "num_format": "0", "locked": False,
            "align": "center", "border": 2, "border_color": gold,
        }),
        "pkg_val": wb.add_format({
            **bd, "bold": True, "font_size": 11, "bg_color": dark,
            "font_color": white, "num_format": '#,##0.00 "zł"',
            "align": "center", "valign": "vcenter", **bdr,
        }),
        "pkg_fill": wb.add_format({"bg_color": dark, **bdr}),
        "t": _f(), "t_a": _f(),
        "tb": _fb(), "tb_a": _fb(),
        "n": _f(align="right"), "n_a": _f(align="right"),
        "p": _fb(num_format='#,##0.00 "zł"', align="right"),
        "p_a": _fb(num_format='#,##0.00 "zł"', align="right"),
        "q": _f(num_format="0", locked=False, align="center"),
        "q_a": _f(num_format="0", locked=False, align="center"),
        "f": _f(num_format="0", align="right"),
        "f_a": _f(num_format="0", align="right"),
        "v": _fb(num_format='#,##0.00 "zł"', align="right"),
        "v_a": _fb(num_format='#,##0.00 "zł"', align="right"),
        "blank": wb.add_format({"bg_color": white, "border": 0}),
    }


def _write_top_bar(ws, fmt: dict, config: dict, last_col: int,
                   value_col: int) -> int:
    catalog = config.get("catalog", {})
    logo_path = config.get("brandbook", {}).get("logo", "")
    logo_full = _PROJECT_ROOT / logo_path if logo_path else None

    ws.merge_range(0, 0, 0, 1, "", fmt["top_bar"])
    label = f"{catalog.get('subtitle', '')}   |   WARTOŚĆ ZAMÓWIENIA NETTO:"
    ws.merge_range(0, 2, 0, value_col - 1, label, fmt["top_bar"])
    ws.write(0, value_col, 0, fmt["top_val"])
    for c in range(value_col + 1, last_col + 1):
        ws.write_blank(0, c, None, fmt["top_bar"])
    ws.set_row(0, 60)

    if logo_full and logo_full.exists():
        sx, sy = _img_scale(str(logo_full), 250, 72)
        ws.insert_image(0, 0, str(logo_full), {
            "x_scale": sx, "y_scale": sy,
            "x_offset": 3, "y_offset": 3, "object_position": 1,
        })
    return 2


def _write_pkg_header(ws, fmt: dict, pkg: dict, row: int, last_col: int,
                      pkg_h: int, standalone: bool = False) -> int:
    name = pkg.get("name", "")
    ws.merge_range(row, 0, row, 3, name, fmt["pkg_bar"])
    if standalone:
        ws.merge_range(row, 4, row, 5, "", fmt["pkg_fill"])
    else:
        ws.write(row, 4, "Zamów pakiety:", fmt["pkg_label"])
        ws.write(row, 5, 0, fmt["pkg_qty"])
        ws.data_validation(row, 5, row, 5, {
            "validate": "integer", "criteria": ">=",
            "value": 0, "error_message": "Ilość pakietów >= 0",
        })
    ws.merge_range(row, 6, row, 7,
                   "Wartość sekcji:" if standalone else "Wartość pakietu:",
                   fmt["pkg_label"])
    for c in range(9, last_col + 1):
        ws.write_blank(row, c, None, fmt["pkg_fill"])
    ws.set_row(row, pkg_h)
    return row + 1


def _write_product_row(
    ws, fmt: dict, row: int, idx: int, item: dict,
    pkg_qty_cell: str, prod_lookup: dict, columns: list, photo_h: int,
) -> None:
    alt = idx % 2 == 1
    t = fmt["t_a"] if alt else fmt["t"]
    tb = fmt["tb_a"] if alt else fmt["tb"]
    n = fmt["n_a"] if alt else fmt["n"]
    p = fmt["p_a"] if alt else fmt["p"]
    q = fmt["q_a"] if alt else fmt["q"]
    f = fmt["f_a"] if alt else fmt["f"]
    v = fmt["v_a"] if alt else fmt["v"]
    r1 = row + 1
    code = item.get("product_code", "")
    prod = prod_lookup.get(code, {})
    price = item.get("unit_price") or prod.get("price_net", 0)
    ean = prod.get("ean", "")
    per_pack_col = _find_col_idx(columns, "per_pack") if any(c.get("key") == "per_pack" for c in columns) else None

    for ci, col_cfg in enumerate(columns):
        key = col_cfg.get("key", "")
        bold = col_cfg.get("bold", False)
        txt = tb if bold else t

        if key == "photo":
            ws.write_blank(row, ci, None, t)
            img = _find_product_image(ean)
            if img:
                sx, sy = _img_scale(img, 95, 115)
                ws.insert_image(row, ci, img, {
                    "x_scale": sx, "y_scale": sy,
                    "x_offset": 2, "y_offset": 2, "object_position": 1,
                })
        elif key == "ean":
            ws.write_string(row, ci, ean, txt)
        elif key == "name":
            ws.write_string(row, ci, item.get("product_name", ""), txt)
        elif key == "price_net":
            ws.write_number(row, ci, price, p)
        elif key == "qty_in_pkg":
            ws.write_number(row, ci, item.get("quantity") or 0, n)
        elif key == "qty_from_pkg":
            qty_col = _col_letter(ci - 1)
            ws.write_formula(row, ci, f"={qty_col}{r1}*{pkg_qty_cell}", f)
        elif key == "qty_extra":
            ws.write_blank(row, ci, None, q)
            ws.data_validation(row, ci, row, ci, {
                "validate": "integer", "criteria": ">=",
                "value": 0, "error_message": "Ilość >= 0",
            })
        elif key == "qty_total":
            extra_col = _col_letter(ci - 1)
            from_col = _col_letter(ci - 2)
            pp_col = _col_letter(per_pack_col) if per_pack_col else None
            if pp_col:
                ws.write_formula(row, ci,
                    f"={from_col}{r1}+{extra_col}{r1}*IF({pp_col}{r1}=\"\",1,{pp_col}{r1})", f)
            else:
                ws.write_formula(row, ci, f"={from_col}{r1}+{extra_col}{r1}", f)
        elif key == "value":
            price_col = _col_letter(_find_col_idx(columns, "price_net"))
            total_col = _col_letter(ci - 1)
            ws.write_formula(row, ci, f"={price_col}{r1}*{total_col}{r1}", v)
        else:
            val = prod.get(key)
            if val is None:
                ws.write_blank(row, ci, None, n)
            elif isinstance(val, (int, float)):
                ws.write_number(row, ci, val, n)
            else:
                ws.write_string(row, ci, str(val), t)

    ws.set_row(row, photo_h)


def _col_letter(idx: int) -> str:
    if idx < 26:
        return chr(65 + idx)
    return chr(64 + idx // 26) + chr(65 + idx % 26)


def _find_col_idx(columns: list, key: str) -> int:
    for i, c in enumerate(columns):
        if c.get("key") == key:
            return i
    return 0


def render_excel(
    products: list, packages: list, config: dict, output_path: str,
) -> str:
    """Generate package-centric order form XLSX from config."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    ec = _excel_cfg(config)
    columns = ec["columns"]
    last_col = len(columns) - 1

    prod_lookup = {p.get("code_xl", ""): p for p in products}
    wb = xlsxwriter.Workbook(str(out))
    ws = wb.add_worksheet("Zamówienie")
    fmt = _xl_formats(wb, config)
    ws.hide_gridlines(2)

    value_ci = _find_col_idx(columns, "value")
    val_letter = _col_letter(value_ci)

    row = _write_top_bar(ws, fmt, config, last_col, value_ci)
    summary_row = 0

    header_row = row
    for ci, col_cfg in enumerate(columns):
        ws.write(row, ci, col_cfg.get("header", ""), fmt["header"])
    row += 1
    data_start_row = row

    from tools.catalog.data_loader import standalone_group_name

    sorted_pkgs = _sort_packages(
        [p for p in packages if p.get("items")], ec["sort_order"])

    # -- Collect codes used in packages --
    pkg_product_codes = set()
    for pkg in sorted_pkgs:
        for item in pkg.get("items", []):
            pkg_product_codes.add(item.get("product_code", ""))

    # -- Build standalone groups --
    standalone = [p for p in products
                  if p.get("code_xl", "") and p["code_xl"] not in pkg_product_codes]
    sa_groups: dict[str, list] = {}
    for p in standalone:
        grp = standalone_group_name(p.get("default_group"), p.get("name", ""))
        sa_groups.setdefault(grp, []).append(p)
    _SORT_BY_PRICE_GROUPS = {"Wkłady LED", "Świece LED"}
    for grp_name, grp_products in sa_groups.items():
        if grp_name in _SORT_BY_PRICE_GROUPS:
            grp_products.sort(key=lambda p: p.get("price_net", 0))
        else:
            grp_products.sort(key=lambda p: p.get("name", ""))

    # -- Render sections in config-defined order (interleaved) --
    section_order = ec.get("section_order")
    pkg_header_rows = []

    def _render_package(pkg):
        nonlocal row
        pkg_row = row
        row = _write_pkg_header(ws, fmt, pkg, row, last_col, ec["pkg_h"])
        pkg_qty_cell = f"${_col_letter(5)}${pkg_row + 1}"
        items = _sort_items(pkg["items"], ec["sort_products"], prod_lookup)
        first_item_row = row
        for i, item in enumerate(items):
            _write_product_row(ws, fmt, row, i, item, pkg_qty_cell,
                               prod_lookup, columns, ec["photo_h"])
            row += 1
        if items:
            ws.write_formula(pkg_row, value_ci,
                f"=SUM({val_letter}{first_item_row+1}:{val_letter}{row})",
                fmt["pkg_val"])
            pkg_header_rows.append(pkg_row)

    def _render_standalone_group(grp_name, grp_products):
        nonlocal row
        pkg_row = row
        standalone_pkg = {"name": grp_name, "code_xl": "", "items": []}
        row = _write_pkg_header(ws, fmt, standalone_pkg, row, last_col, ec["pkg_h"],
                                standalone=True)
        first_item_row = row
        for i, p in enumerate(grp_products):
            item = {
                "product_code": p["code_xl"],
                "product_name": p.get("name", ""),
                "quantity": 0,
                "unit_price": p.get("price_net", 0),
            }
            _write_product_row(ws, fmt, row, i, item, "0",
                               prod_lookup, columns, ec["photo_h"])
            row += 1
        ws.write_formula(pkg_row, value_ci,
            f"=SUM({val_letter}{first_item_row+1}:{val_letter}{row})",
            fmt["pkg_val"])
        pkg_header_rows.append(pkg_row)

    if section_order:
        used_pkgs = set()
        used_sa = set()
        for section in section_order:
            if section["type"] == "packages":
                match_list = [m.upper() for m in section.get("match", [])]
                for pkg in sorted_pkgs:
                    pname = (pkg.get("name") or "").upper()
                    if any(m in pname for m in match_list) and id(pkg) not in used_pkgs:
                        _render_package(pkg)
                        used_pkgs.add(id(pkg))
            elif section["type"] == "standalone":
                for grp_name in section.get("groups", []):
                    if grp_name in sa_groups and grp_name not in used_sa:
                        _render_standalone_group(grp_name, sa_groups[grp_name])
                        used_sa.add(grp_name)
        # Render any remaining packages/standalone not matched by section_order
        for pkg in sorted_pkgs:
            if id(pkg) not in used_pkgs:
                _render_package(pkg)
        for grp_name, grp_products in sa_groups.items():
            if grp_name not in used_sa:
                _render_standalone_group(grp_name, grp_products)
    else:
        # Fallback: all packages then all standalone
        for pkg in sorted_pkgs:
            _render_package(pkg)
        for grp_name, grp_products in sa_groups.items():
            _render_standalone_group(grp_name, grp_products)

    # Sum only section header rows (not products) to avoid double-counting
    if pkg_header_rows:
        pkg_cells = "+".join(f"{val_letter}{r + 1}" for r in pkg_header_rows)
        ws.write_formula(summary_row, value_ci, f"={pkg_cells}", fmt["top_val"])
    else:
        ws.write_number(summary_row, value_ci, 0, fmt["top_val"])

    for ci, col_cfg in enumerate(columns):
        ws.set_column(ci, ci, col_cfg.get("width", 12))

    last_data_row = row - 1 if row > header_row + 1 else header_row + 1
    ws.autofilter(header_row, 0, last_data_row, last_col)
    ws.freeze_panes(header_row + 1, 0)
    ws.protect("", {
        "objects": True,
        "scenarios": True,
        "autofilter": True,
        "sort": True,
        "select_unlocked_cells": True,
        "select_locked_cells": True,
    })
    ws.set_landscape()
    ws.set_paper(9)
    ws.fit_to_pages(1, 0)
    ws.repeat_rows(header_row, header_row)

    wb.close()
    return str(out.resolve())

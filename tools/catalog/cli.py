"""Catalog CLI — generate product catalogs from config + data.

Usage:
    py tools/catalog/cli.py render-html --config config/catalogs/ceim_brico_2025.yaml
    py tools/catalog/cli.py render-html --config config/catalogs/ceim_brico_2025.yaml --open
"""

import argparse
import json
import sys
import webbrowser
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent  # Auto-ERP-Agent root
sys.path.insert(0, str(PROJECT_ROOT))

from tools.catalog.data_loader import load_mock_data, load_erp_data, category_for_package
from tools.catalog.renderers import render_html, render_excel, write_html


def _load_data(config: dict) -> tuple[list, list]:
    data_cfg = config.get("data", {})
    dtype = data_cfg.get("type", "mock")
    if dtype == "mock":
        return load_mock_data(
            str(PROJECT_ROOT / data_cfg["products_path"]),
            str(PROJECT_ROOT / data_cfg["packages_path"]),
        )
    if dtype == "erp_export":
        return load_erp_data(
            str(PROJECT_ROOT / data_cfg["products_path"]),
            str(PROJECT_ROOT / data_cfg["packages_path"]),
            data_cfg.get("package_filter"),
        )
    print(json.dumps({"ok": False, "error": f"Unsupported data type: {dtype}"}))
    sys.exit(1)


def cmd_render_html(args):
    config_path = PROJECT_ROOT / args.config
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    products, packages = _load_data(config)

    html = render_html(products, packages, config, category_for_package)
    output_path = config.get("outputs", {}).get("html", {}).get("path", "output/catalog.html")
    full_path = write_html(html, str(PROJECT_ROOT / output_path))

    result = {
        "ok": True,
        "output": full_path,
        "products": len(products),
        "packages": len(packages),
        "size_kb": round(Path(full_path).stat().st_size / 1024, 1),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.open:
        webbrowser.open(f"file://{full_path}")


def cmd_render_excel(args):
    config_path = PROJECT_ROOT / args.config
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    products, packages = _load_data(config)

    output_path = config.get("outputs", {}).get("excel", {}).get("path", "output/catalog.xlsx")
    full_path = render_excel(products, packages, config, str(PROJECT_ROOT / output_path))

    result = {
        "ok": True,
        "output": full_path,
        "products": len(products),
        "packages": len(packages),
        "size_kb": round(Path(full_path).stat().st_size / 1024, 1),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.open:
        webbrowser.open(f"file://{full_path}")


def main():
    parser = argparse.ArgumentParser(description="Catalog generator CLI")
    sub = parser.add_subparsers(dest="command")

    html_p = sub.add_parser("render-html", help="Generate interactive HTML catalog")
    html_p.add_argument("--config", required=True, help="Path to YAML config")
    html_p.add_argument("--open", action="store_true", help="Open in browser after render")

    excel_p = sub.add_parser("render-excel", help="Generate Excel order form")
    excel_p.add_argument("--config", required=True, help="Path to YAML config")
    excel_p.add_argument("--open", action="store_true", help="Open after render")

    args = parser.parse_args()
    if args.command == "render-html":
        cmd_render_html(args)
    elif args.command == "render-excel":
        cmd_render_excel(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

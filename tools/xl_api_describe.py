"""Wypisuje pola struct dla metod XL API przez XlProxy describe.

Nie wymaga zalogowanej sesji ERP — tylko załadowania DLL.
Użycie:
  python tools/xl_api_describe.py XLNowyDokument XLDodajPozycje XLZamknijDokument
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import os

load_dotenv()

from tools.lib.xl_proxy_client import XlProxyClient

_DLL_DIR = os.environ.get("XL_DLL_DIR", r"C:\Comarch ERP\Comarch ERP XL 2025.1")


def describe(methods: list[str]) -> None:
    client = XlProxyClient(_DLL_DIR)
    client.start()
    try:
        for method in methods:
            result = client.send({"cmd": "describe", "method": method})
            if not result.get("ok"):
                print(f"ERROR {method}: {result}")
                continue
            print(f"\n=== {method} ===")
            for param in result.get("params", []):
                byref = " [out]" if param.get("byref") else ""
                print(f"  {param['name']}: {param['type']}{byref}")
                for field in param.get("fields", []):
                    print(f"    .{field['name']}: {field['type']}")
    finally:
        client.stop()


if __name__ == "__main__":
    methods = sys.argv[1:] or ["XLNowyDokument", "XLDodajPozycje", "XLZamknijDokument"]
    describe(methods)

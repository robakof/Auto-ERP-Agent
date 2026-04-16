"""Unit tests xsd_validator — walidacja XML przeciw XSD."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from core.ksef.adapters.xml_builder import XmlBuilder
from core.ksef.adapters.xsd_validator import validate
from tests.ksef.fixtures.domain_samples import make_fs_59, make_fsk_1


_XSD_MINIMAL = b"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Root">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="Name" type="xs:string"/>
        <xs:element name="Age" type="xs:integer"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
"""


def test_valid_xml_returns_true_empty_errors(tmp_path: Path) -> None:
    xsd = tmp_path / "schema.xsd"
    xsd.write_bytes(_XSD_MINIMAL)
    xml = b'<Root><Name>Alice</Name><Age>30</Age></Root>'
    valid, errors = validate(xml, xsd)
    assert valid is True
    assert errors == []


def test_invalid_xml_returns_false_with_errors(tmp_path: Path) -> None:
    xsd = tmp_path / "schema.xsd"
    xsd.write_bytes(_XSD_MINIMAL)
    xml = b'<Root><Name>Alice</Name><Age>not_a_number</Age></Root>'
    valid, errors = validate(xml, xsd)
    assert valid is False
    assert len(errors) >= 1
    assert errors[0].startswith("Linia ")


def test_missing_xsd_raises_file_not_found(tmp_path: Path) -> None:
    xsd = tmp_path / "missing.xsd"
    xml = b'<Root/>'
    with pytest.raises(FileNotFoundError):
        validate(xml, xsd)


# --- XSD regression tests (W1: real FA(3) schema) ---

_XSD_FA3 = Path(__file__).resolve().parents[2] / "output" / "schemat.xsd"
_CLOCK = lambda: datetime(2026, 4, 14, 12, 0, 0)


@pytest.mark.skipif(not _XSD_FA3.exists(), reason="XSD schemat.xsd not available")
def test_fs_validates_against_fa3_xsd() -> None:
    """FS snapshot XML must pass FA(3) XSD validation."""
    builder = XmlBuilder(clock=_CLOCK)
    xml_bytes = builder.build_faktura(make_fs_59())
    valid, errors = validate(xml_bytes, _XSD_FA3)
    assert valid, f"FS XSD errors: {errors}"


@pytest.mark.skipif(not _XSD_FA3.exists(), reason="XSD schemat.xsd not available")
def test_fsk_validates_against_fa3_xsd() -> None:
    """FSK snapshot XML must pass FA(3) XSD validation."""
    builder = XmlBuilder(clock=_CLOCK)
    xml_bytes = builder.build_korekta(make_fsk_1())
    valid, errors = validate(xml_bytes, _XSD_FA3)
    assert valid, f"FSK XSD errors: {errors}"

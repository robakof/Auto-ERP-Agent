"""Unit tests xsd_validator — walidacja XML przeciw XSD."""
from __future__ import annotations

from pathlib import Path

import pytest

from core.ksef.adapters.xsd_validator import validate


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

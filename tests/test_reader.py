"""Tests für io/reader.py"""
import numpy as np
import pytest
from data_reconciliation.io.reader import read_excel


def test_read_excel_shape(tmp_path):
    """Smoke-Test: Excel-File einlesen und Shapes prüfen."""
    import openpyxl
    wb = openpyxl.Workbook()

    # Worksheet 1
    ws1 = wb.active
    ws1.title = "Stromdaten"
    ws1.append(["Strom-Nr.", 4, 5, 16])   # Stream IDs
    ws1.append(["RHO",       0.02, 0.05, 0.02])
    ws1.append(["",          1000, 20, 10000])
    ws1.append(["",          1001, 21, 10001])

    # Worksheet 2
    ws2 = wb.create_sheet("Matrix_A")
    ws2.append(["Bilanzraum", 4, 5, 16])
    ws2.append(["Gesamt",     1, 1, -1])

    path = tmp_path / "test.xlsx"
    wb.save(path)

    result = read_excel(str(path))
    assert result["X"].shape   == (2, 3)
    assert result["A"].shape   == (1, 3)
    assert result["rho"].shape == (3,)
    assert result["stream_ids"] == [4, 5, 16]

"""
io/reader.py

Liest Rohdaten für die Datenrekonziliation aus dem Excel-File.

Erwartetes Format:
    Worksheet 1 (Stromdaten):
        Zeile 1: Strom-Nummern (ab Spalte 2), z.B. "S4", "S5" oder 4, 5
        Zeile 2: Relative Unsicherheiten RHO = sigma/x (ab Spalte 2)
        Zeile 3+: Messdaten in kg/h

    Worksheet 2 (Matrix_A):
        Zeile 1:   Strom-Nummern (ab Spalte 2)
        Spalte 1:  Bezeichnungen der Bilanzräume (ab Zeile 2)
        Zeile 2+:  Einträge der Matrix A (+1, 0, -1)

    Worksheet 3 (Strombezeichnungen, optional):
        Zeile 1:   Header (Strom-Nr., Klarname, Nominaler Wert, Einheit, Typ)
        Zeile 2+:  Eine Zeile je Strom
        Rückgabe als dict {stream_id (int): {klarname, nominal, einheit, typ}}
"""

import numpy as np
import pandas as pd


def _parse_stream_id(val) -> int:
    """Konvertiert Strom-ID zu int, akzeptiert '4', 'S4', 4 etc."""
    s = str(val).strip()
    if s.upper().startswith("S"):
        s = s[1:]
    return int(float(s))


def read_excel(path: str) -> dict:
    """
    Liest Stromdaten, Matrix A und (optional) Strombezeichnungen
    aus dem Excel-File.

    Args:
        path: Pfad zur Excel-Datei

    Returns:
        {
          'stream_ids':        list[int]        – Strom-Nummern [4, 5, ...]
          'rho':               np.ndarray       – (N,) relative Unsicherheiten
          'X':                 np.ndarray       – (k, N) Messdaten in kg/h
          'A':                 np.ndarray       – (M, N) Bilanzmatrix
          'balance_ids':       list[str]        – Bezeichnungen der Bilanzräume
          'stream_labels':     dict | None      – {int: dict} Klarname etc.,
                                                  None wenn Sheet nicht vorhanden
        }
    """
    # Worksheet 1: Stromdaten
    df1 = pd.read_excel(path, sheet_name=0, header=None)
    stream_ids = [_parse_stream_id(v) for v in df1.iloc[0, 1:]]
    rho        = df1.iloc[1, 1:].astype(float).values        # (N,)
    X          = df1.iloc[2:,  1:].astype(float).values      # (k, N)

    # Worksheet 2: Matrix A
    df2         = pd.read_excel(path, sheet_name=1, header=None)
    balance_ids = df2.iloc[1:, 0].tolist()
    A           = df2.iloc[1:, 1:].astype(float).values      # (M, N)

    # Worksheet 3: Strombezeichnungen (optional)
    xl          = pd.ExcelFile(path)
    stream_labels = None
    if len(xl.sheet_names) >= 3:
        df3 = pd.read_excel(path, sheet_name=2, header=0)
        stream_labels = {}
        for _, row in df3.iterrows():
            sid = _parse_stream_id(row.iloc[0])
            stream_labels[sid] = {
                "klarname": str(row.iloc[1]),
                "nominal":  float(row.iloc[2]),
                "einheit":  str(row.iloc[3]),
                "typ":      str(row.iloc[4]),
            }

    return {
        "stream_ids":    stream_ids,
        "rho":           rho,
        "X":             X,
        "A":             A,
        "balance_ids":   balance_ids,
        "stream_labels": stream_labels,
    }
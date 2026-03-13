"""
reconciliation/balance.py

Berechnung des rohen Massenbilanz-Fehlers aus Stromdaten und Bilanzmatrix A,
sowie tabellarische Auswertung via BalanceReport.

Mathematischer Hintergrund:
    Für k Zeitschritte und M Bilanzräume gilt:

        R = X · A^T     (k × M)

    wobei R[t, m] den Bilanzfehler im Zeitschritt t für Bilanzraum m angibt.
    Bei einer idealen, geschlossenen Massenbilanz gilt R ≈ 0.

    Der Mittelwert über alle Zeitschritte:

        R_mean = R.mean(axis=0)     (M,)

    dient als Diagnosegröße für systematische Bilanzfehler je Bilanzraum,
    z.B. durch Fehlkalibrierung oder Gross Errors.

    Metriken im Report:
        Input           = Mittelwert der Summe aller Ströme mit A-Koeffizient +1
        Output          = Mittelwert der Summe aller Ströme mit A-Koeffizient -1
        Residual (abs.) = Output - Input  [negativ → Output < Input]
        Residual (rel.) = Residual (abs.) / Input × 100 %

Hinweis:
    compute_mass_balance() ist eine reine Rechenfunktion ohne Seiteneffekte.
    BalanceReport nutzt sie intern und verwaltet mehrere Datensätze über
    eine Session.

CUDA-Erweiterung:
    numpy durch cupy ersetzen:
        import cupy as np   # drop-in replacement
"""

import numpy as np
import pandas as pd
from collections import OrderedDict


# ---------------------------------------------------------------------------
# Kernfunktion
# ---------------------------------------------------------------------------

def compute_mass_balance(
    X: np.ndarray,
    A: np.ndarray,
) -> dict:
    """
    Berechnet den Massenbilanz-Fehler (Residual) aus Stromdaten und Matrix A.

    Der Bilanzfehler R = X · A^T gibt an, wie weit die gemessenen Ströme
    die Bilanzgleichungen A · x = 0 verletzen. Eine geschlossene Bilanz
    ergibt R ≈ 0.

    Die Funktion ist generalisierbar: Sie kann für beliebige Inputs aufgerufen
    werden, z.B. einmal für Rohdaten X und einmal für gefilterte Daten X_stat.
    Labels (balance_ids) liegen beim Aufrufer und werden nicht durchgereicht.

    Args:
        X: (k, N) Messdaten – kann Rohdaten oder gefilterte Daten sein
        A: (M, N) Bilanzmatrix mit Einträgen {-1, 0, +1}

    Returns:
        {
          'residuals':      np.ndarray  – (k, M) Bilanzfehler je Zeitschritt
                                         und Bilanzraum
          'residuals_mean': np.ndarray  – (M,) Mittlerer Bilanzfehler je
                                         Bilanzraum über alle k Zeitschritte
        }

    Beispiel:
        >>> balance_raw  = compute_mass_balance(X,      A)
        >>> balance_stat = compute_mass_balance(X_stat, A)
    """
    residuals      = X @ A.T                 # (k, M)
    residuals_mean = residuals.mean(axis=0)  # (M,)

    return {
        "residuals":      residuals,
        "residuals_mean": residuals_mean,
    }


# ---------------------------------------------------------------------------
# Hilfsfunktion
# ---------------------------------------------------------------------------

def _fmt(val: float) -> float:
    """
    Adaptive Rundung: |val| >= 100 → 0 Dezimalstellen, sonst 2.
    Gibt float zurück damit pandas den Typ einheitlich hält.
    """
    decimals = 0 if abs(val) >= 100 else 2
    return round(val, decimals)


# ---------------------------------------------------------------------------
# Report-Klasse
# ---------------------------------------------------------------------------

class BalanceReport:
    """
    Tabellarische Auswertung der Massenbilanz für mehrere Datensätze.

    Verwaltet eine geordnete Sammlung von X-Datensätzen (z.B. Rohdaten,
    gefilterte Daten, rekonziliierte Daten) und gibt für jeden Datensatz
    und jeden Bilanzraum die zentralen Bilanzmetriken als DataFrame aus.

    Metriken je Bilanzraum und Datensatz:
        N               – Anzahl Zeitschritte k
        Input           – Mittlere Summe der Eingangsströme (A-Koeff. = +1)
        Output          – Mittlere Summe der Ausgangsströme (A-Koeff. = -1)
        Residual (abs.) – Output - Input  [negativ → Output < Input]
        Residual (rel.) – Residual (abs.) / Input × 100 %

    Args:
        A:             (M, N) Bilanzmatrix mit Einträgen {-1, 0, +1}
        balance_names: list[str] | None – Bezeichnungen der Bilanzräume.
                       Muss len(balance_names) == A.shape[0] erfüllen.
                       None → automatische Nummerierung: Bilanz_0, Bilanz_1, ...
        eng_unit:      str | None – Einheit der Messgröße, z.B. 'kg/h'.
                       None → Spaltenheader zeigt '[eng_unit]' als Platzhalter.

    Beispiel:
        >>> report = BalanceReport(A, balance_names=["Gesamt"], eng_unit="kg/h")
        >>> report.add("Rohdaten",     X)
        >>> report.add("Gefiltert",    X_stat)
        >>> report.add("Rekonziliert", X_rec)
        >>> report.table()                       # DataFrame im Notebook
        >>> print(report.table())                # Textausgabe in der Konsole
        >>> report.table().loc[["Gesamt"]]       # einzelne Bilanz nach Name
        >>> report.table().iloc[[0]]             # einzelne Bilanz nach Index
        >>> report.reset()                       # Datensätze löschen
    """

    def __init__(self,
                 A: np.ndarray,
                 balance_names: list | None = None,
                 eng_unit: str | None = None):

        self._A          = A
        self._M, self._N = A.shape
        self._unit       = f"[{eng_unit}]" if eng_unit else "[eng_unit]"

        # balance_names validieren oder generieren
        if balance_names is not None:
            if len(balance_names) != self._M:
                raise ValueError(
                    f"balance_names hat {len(balance_names)} Einträge, "
                    f"aber A hat {self._M} Zeilen (Bilanzräume). "
                    f"Die Anzahl muss übereinstimmen."
                )
            self._balance_names = list(balance_names)
        else:
            self._balance_names = [f"Bilanz_{m}" for m in range(self._M)]

        # Geordnetes Dict: label → X (Reihenfolge = add()-Calls)
        self._datasets: OrderedDict[str, np.ndarray] = OrderedDict()

        # Masken für Ein- und Ausgangsströme je Bilanzraum (einmal berechnen)
        self._mask_in  = (A > 0)  # (M, N) bool
        self._mask_out = (A < 0)  # (M, N) bool

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def add(self, label: str, X: np.ndarray, overwrite: bool = False) -> None:
        """
        Fügt einen Datensatz zur Auswertung hinzu.

        Args:
            label:     Bezeichnung des Datensatzes (Spaltenname im Report)
            X:         (k, N) Messdaten
            overwrite: True → vorhandenes Label wird stillschweigend
                       überschrieben (Standard: False)
        """
        # Dimensionsprüfung
        if X.shape[1] != self._N:
            raise ValueError(
                f"X hat {X.shape[1]} Spalten (Ströme), "
                f"aber A erwartet {self._N} Spalten. "
                f"Dimensionen müssen übereinstimmen."
            )

        # Label-Kollision
        if label in self._datasets:
            if overwrite:
                self._datasets[label] = X
                print(f"[BalanceReport] '{label}' wurde überschrieben.")
            else:
                print(
                    f"[BalanceReport] Label '{label}' ist bereits vorhanden – "
                    f"Datensatz wurde nicht hinzugefügt.\n"
                    f"               Nutze add('{label}', X, overwrite=True) "
                    f"zum Überschreiben."
                )
            return

        self._datasets[label] = X

    def reset(self) -> None:
        """
        Löscht alle Datensätze. A und balance_names bleiben erhalten.
        """
        self._datasets.clear()
        print("[BalanceReport] Alle Datensätze gelöscht.")

    def table(self) -> pd.DataFrame:
        """
        Berechnet die Bilanzmetriken und gibt sie als DataFrame zurück.

        Zeilen:   Bilanzräume (balance_names)
        Spalten:  MultiIndex (Datensatz-Label, Metrik)

        Returns:
            pd.DataFrame mit den Bilanzmetriken für alle Datensätze.

        Hinweise zur Ausgabe:
            Im Jupyter Notebook wird der DataFrame ohne print() als
            formatierte Tabelle gerendert.
            Für Konsolenausgabe:        print(report.table())
            Für eine Bilanz nach Name:  report.table().loc[["Gesamt"]]
            Für eine Bilanz nach Index: report.table().iloc[[0]]
        """
        if not self._datasets:
            print(
                "[BalanceReport] Keine Datensätze vorhanden. "
                "Nutze add(label, X) um Datensätze hinzuzufügen."
            )
            return pd.DataFrame()

        unit = self._unit
        metric_labels = [
            "N",
            f"Input {unit}",
            f"Output {unit}",
            f"Residual abs. {unit}",
            "Residual rel. [%]",
        ]
        dataset_labels = list(self._datasets.keys())

        # Zeilenindex: bei M=1 nur Metriken; bei M>1 MultiIndex (Bilanzraum, Metrik)
        if self._M == 1:
            index = pd.Index(metric_labels, name="Metrik")
        else:
            index = pd.MultiIndex.from_product(
                [self._balance_names, metric_labels],
                names=["Bilanzraum", "Metrik"],
            )

        df = pd.DataFrame(
            index=index,
            columns=pd.Index(dataset_labels, name="Datensatz"),
            dtype=float,
        )

        for label, X in self._datasets.items():
            k = X.shape[0]

            for m, bname in enumerate(self._balance_names):
                X_in  = X[:, self._mask_in[m]]
                X_out = X[:, self._mask_out[m]]

                mean_in  = X_in.sum(axis=1).mean()  if X_in.size  > 0 else 0.0
                mean_out = X_out.sum(axis=1).mean() if X_out.size > 0 else 0.0

                res_abs = mean_out - mean_in
                res_rel = (res_abs / mean_in * 100) if mean_in != 0 else float("nan")

                row = bname if self._M > 1 else slice(None)

                def _set(metric, val):
                    if self._M == 1:
                        df.loc[metric, label] = val
                    else:
                        df.loc[(bname, metric), label] = val

                _set("N",                          int(k))
                _set(f"Input {unit}",              _fmt(mean_in))
                _set(f"Output {unit}",             _fmt(mean_out))
                _set(f"Residual abs. {unit}",      _fmt(res_abs))
                _set("Residual rel. [%]",          round(res_rel, 2))

        return df

    # -----------------------------------------------------------------------
    # Repr
    # -----------------------------------------------------------------------

    def __repr__(self) -> str:
        datasets = list(self._datasets.keys()) or ["–"]
        return (
            f"BalanceReport("
            f"Bilanzräume={self._balance_names}, "
            f"Datensätze={datasets}, "
            f"Einheit={self._unit})"
        )
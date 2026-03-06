"""
preprocessing/filter.py

Filtert instationäre Zeitschritte vor der Datenrekonziliation.

Verfügbare Filter:
    IQRFilter       - Strom-weise Tukey-Fences (+-k*IQR)
    ResidualFilter  - Bilanzfehler A*x(t) vs. Referenz-Statistik
    CompositeFilter - Kombiniert mehrere Filter (AND / OR)

Verwendung:
    from data_reconciliation.preprocessing.filter import (
        IQRFilter, ResidualFilter, CompositeFilter, filter_report
    )

    f = CompositeFilter([
            IQRFilter(k=1.5),
            ResidualFilter(A, threshold=3.0)
        ], mode='and')

    mask           = f.fit_transform(X)
    X_stationary   = X[mask]
    filter_report(mask)
"""

import numpy as np
from abc import ABC, abstractmethod


# ---------------------------------------------------------------------------
# Abstrakte Basisklasse
# ---------------------------------------------------------------------------

class BaseFilter(ABC):
    """Gemeinsame Schnittstelle für alle Instationaritäts-Filter."""

    @abstractmethod
    def fit(self, X: np.ndarray) -> "BaseFilter":
        """Berechnet Filter-Parameter aus den Daten."""
        ...

    @abstractmethod
    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Gibt boolean-Maske zurück.
        True  = stationär  -> für DR verwenden
        False = instationär -> ausschließen
        """
        ...

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)


# ---------------------------------------------------------------------------
# Filter 1: IQR-basiert (Tukey-Fences)
# ---------------------------------------------------------------------------

class IQRFilter(BaseFilter):
    """
    Markiert Zeitschritte als instationär, bei denen mindestens ein Strom
    außerhalb von [Q25 - k*IQR,  Q75 + k*IQR] liegt.

    k=1.5  -> klassischer Tukey-Ansatz (~+-2.7 sigma bei Normalverteilung)
    k=3.0  -> nur extreme Ausreißer ("far outliers")

    Gut geeignet für: Anlagenstillstände, drastische Abfälle einzelner
    Ströme (z.B. KW1-Stillstand). Grenzen werden je Strom separat aus
    den Trainingsdaten berechnet.

    Limitation: Wenn Input- UND Output-Ströme gleichzeitig proportional
    driften (Bilanz bleibt formal geschlossen), kann dieser Filter die
    Instationarität ggf. nicht erkennen -> ResidualFilter kombinieren.

    Args:
        k: Tukey-Multiplikator (Standard: 1.5)
    """

    def __init__(self, k: float = 1.5):
        self.k = k
        self._lower = None
        self._upper = None

    def fit(self, X: np.ndarray) -> "IQRFilter":
        q25 = np.percentile(X, 25, axis=0)   # (N,)
        q75 = np.percentile(X, 75, axis=0)   # (N,)
        iqr          = q75 - q25
        self._lower  = q25 - self.k * iqr
        self._upper  = q75 + self.k * iqr
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self._lower is None:
            raise RuntimeError("fit() muss vor transform() aufgerufen werden.")
        within = (X >= self._lower) & (X <= self._upper)  # (k, N)
        return within.all(axis=1)                          # (k,)

    @property
    def bounds(self) -> dict:
        return {"lower": self._lower, "upper": self._upper}


# ---------------------------------------------------------------------------
# Filter 2: Bilanzfehler-basiert
# ---------------------------------------------------------------------------

class ResidualFilter(BaseFilter):
    """
    Markiert Zeitschritte als instationär, bei denen der Bilanzfehler
    r(t) = A*x(t) mehr als `threshold` Standardabweichungen vom
    Referenz-Mittelwert abweicht.

    Ergänzt den IQRFilter für schleichende Imbalancen oder Fälle,
    in denen alle Ströme gleichzeitig driften.

    Args:
        A:            (M, N) Bilanzmatrix
        threshold:    Schwellwert in Vielfachen der Referenz-Stdabw.
        ref_fraction: Anteil der Daten für Referenzstatistik (erste X%)
        ref_window:   Explizites Referenzfenster (start, end) als Tupel
    """

    def __init__(self, A: np.ndarray, threshold: float = 3.0,
                 ref_fraction: float = 0.8,
                 ref_window=None):
        self.A            = A
        self.threshold    = threshold
        self.ref_fraction = ref_fraction
        self.ref_window   = ref_window
        self._ref_mean    = None
        self._ref_std     = None

    def fit(self, X: np.ndarray) -> "ResidualFilter":
        residuals = X @ self.A.T   # (k, M)
        k         = X.shape[0]

        start, end = (self.ref_window if self.ref_window
                      else (0, int(self.ref_fraction * k)))

        ref            = residuals[start:end]
        self._ref_mean = ref.mean(axis=0)
        self._ref_std  = np.where(ref.std(axis=0) < 1e-10, 1e-10,
                                  ref.std(axis=0))
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self._ref_mean is None:
            raise RuntimeError("fit() muss vor transform() aufgerufen werden.")
        residuals = X @ self.A.T
        z_scores  = np.abs(residuals - self._ref_mean) / self._ref_std
        return (z_scores < self.threshold).all(axis=1)


# ---------------------------------------------------------------------------
# Filter 3: Komposit-Filter
# ---------------------------------------------------------------------------

class CompositeFilter(BaseFilter):
    """
    Kombiniert mehrere Filter-Instanzen mit AND- oder OR-Logik.

    mode='and': stationär, wenn ALLE Filter zustimmen  (empfohlen)
    mode='or':  stationär, wenn MINDESTENS EIN Filter zustimmt

    Args:
        filters: Liste von BaseFilter-Instanzen
        mode:    'and' oder 'or'
    """

    def __init__(self, filters: list, mode: str = "and"):
        assert mode in ("and", "or"), "mode muss 'and' oder 'or' sein."
        self.filters = filters
        self.mode    = mode

    def fit(self, X: np.ndarray) -> "CompositeFilter":
        for f in self.filters:
            f.fit(X)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        masks = np.stack([f.transform(X) for f in self.filters], axis=1)
        return masks.all(axis=1) if self.mode == "and" else masks.any(axis=1)

    def transform_detailed(self, X: np.ndarray) -> dict:
        """
        Gibt Einzelmasken jedes Filters zurück - nützlich zur Diagnose,
        welcher Filter wie viele Zeitschritte entfernt.

        Returns:
            dict mit Filtername -> boolean-Maske, plus 'combined'
        """
        masks = {type(f).__name__: f.transform(X) for f in self.filters}
        stacked = np.stack(list(masks.values()), axis=1)
        masks["combined"] = (stacked.all(axis=1) if self.mode == "and"
                             else stacked.any(axis=1))
        return masks


# ---------------------------------------------------------------------------
# Hilfsfunktion: Konsolen-Report
# ---------------------------------------------------------------------------

def filter_report(mask: np.ndarray, detailed_masks: dict = None) -> None:
    """Gibt einen kurzen Report über die Filterung auf der Konsole aus."""
    n       = len(mask)
    kept    = int(mask.sum())
    removed = n - kept

    print("-" * 45)
    print(f"  Filterung: {n} Zeitschritte total")
    print(f"  Behalten:  {kept}  ({100*kept/n:.1f}%)")
    print(f"  Entfernt:  {removed}  ({100*removed/n:.1f}%)")
    if detailed_masks:
        print("  Einzelfilter:")
        for name, m in detailed_masks.items():
            if name == "combined":
                continue
            r = int((~m).sum())
            print(f"    {name}: {r} entfernt ({100*r/n:.1f}%)")
    print("-" * 45)
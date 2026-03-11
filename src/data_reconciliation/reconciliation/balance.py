"""
reconciliation/balance.py

Berechnung des rohen Massenbilanz-Fehlers aus Stromdaten und Bilanzmatrix A.

Mathematischer Hintergrund:
    Für k Zeitschritte und M Bilanzräume gilt:

        R = X · A^T     (k × M)

    wobei R[t, m] den Bilanzfehler im Zeitschritt t für Bilanzraum m angibt.
    Bei einer idealen, geschlossenen Massenbilanz gilt R ≈ 0.

    Der Mittelwert über alle Zeitschritte:

        R_mean = R.mean(axis=0)     (M,)

    dient als Diagnosegröße für systematische Bilanzfehler je Bilanzraum,
    z.B. durch Fehlkalibrierung oder Gross Errors.

Hinweis:
    Diese Funktion bewertet die Rohdaten (oder gefilterten Daten) vor der
    Rekonziliation. Sie ist unabhängig von reconcile.py und kann für beliebige
    X-Inputs aufgerufen werden (mehrfach mit verschiedenen Inputs möglich).

CUDA-Erweiterung:
    numpy durch cupy ersetzen:
        import cupy as np   # drop-in replacement
"""

import numpy as np


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
        X: (k, N) Messdaten in kg/h – kann Rohdaten oder gefilterte Daten sein
        A: (M, N) Bilanzmatrix mit Einträgen {-1, 0, +1}

    Returns:
        {
          'residuals':      np.ndarray  – (k, M) Bilanzfehler je Zeitschritt
                                         und Bilanzraum [kg/h]
          'residuals_mean': np.ndarray  – (M,) Mittlerer Bilanzfehler je
                                         Bilanzraum über alle k Zeitschritte
                                         [kg/h]
        }

    Beispiel:
        >>> balance_raw  = compute_mass_balance(X,      A)
        >>> balance_stat = compute_mass_balance(X_stat, A)
    """
    residuals      = X @ A.T                # (k, M)
    residuals_mean = residuals.mean(axis=0) # (M,)

    return {
        "residuals":      residuals,
        "residuals_mean": residuals_mean,
    }
"""
reconciliation/reconcile.py

Lineare stationäre Datenrekonziliation für k simultane Zeitschritte.

Mathematischer Hintergrund:
    Gegeben Messdaten X (k×N), Bilanzmatrix A (M×N), Kovarianzmatrix Q (N×N).
    Gesucht: X_hat mit A·X_hat = 0 und minimalem gewichteten Fehler.

    Analytische Lösung (Lagrange):
        delta_X = -X · P^T
        P       = Q · A^T · (A·Q·A^T + lambda·I)^{-1} · A
        X_hat   = X + delta_X

    Die Projektionsmatrix P wird einmal berechnet und auf alle k
    Zeitschritte angewendet (simultane Matrix-Operation).

CUDA-Erweiterung:
    numpy durch cupy ersetzen:
        import cupy as np   # drop-in replacement
"""

import numpy as np


def build_projection_matrix(A: np.ndarray, rho: np.ndarray,
                             x_mean: np.ndarray,
                             lam: float = 0.0) -> np.ndarray:
    """
    Berechnet die Projektionsmatrix P = Q·A^T·(A·Q·A^T + lam·I)^{-1}·A.

    Args:
        A:      (M, N) Bilanzmatrix
        rho:    (N,)   relative Unsicherheiten sigma/x
        x_mean: (N,)   mittlere Stromwerte (zur Varianzberechnung)
        lam:    Regularisierungsparameter (Tikhonov), Standard=0

    Returns:
        P: (N, N) Projektionsmatrix
    """
    sigma2 = (rho * x_mean) ** 2          # (N,)
    Q      = np.diag(sigma2)              # (N, N)
    M      = A.shape[0]

    AQAt     = A @ Q @ A.T               # (M, M)
    AQAt_reg = AQAt + lam * np.eye(M)
    AQAt_inv = np.linalg.inv(AQAt_reg)   # (M, M)

    return Q @ A.T @ AQAt_inv @ A        # (N, N)


def reconcile(X: np.ndarray, A: np.ndarray, rho: np.ndarray,
              lam: float = 0.0) -> dict:
    """
    Führt Datenrekonziliation für alle k Zeitschritte simultan durch.

    Args:
        X:   (k, N) Messdaten in kg/h
        A:   (M, N) Bilanzmatrix
        rho: (N,)   relative Unsicherheiten sigma/x
        lam: Regularisierungsparameter (Standard: 0.0, kein Einfluss)

    Returns:
        {
          'X_rec':     (k, N)  rekonziliierte Werte,
          'delta_X':   (k, N)  Korrekturen (X_rec - X),
          'residuals': (k, M)  Bilanzfehler nach DR (sollte ≈ 0 sein),
          'SS_res':    (k,)    Sum of Squares der Residuale je Zeitschritt
        }
    """
    x_mean = X.mean(axis=0)                     # (N,)
    P      = build_projection_matrix(A, rho, x_mean, lam)

    delta_X   = -(X @ P.T)                      # (k, N)
    X_rec     = X + delta_X                     # (k, N)
    residuals = X_rec @ A.T                     # (k, M)  → sollte ≈ 0
    SS_res    = np.sum(residuals ** 2, axis=1)  # (k,)

    return {
        "X_rec":     X_rec,
        "delta_X":   delta_X,
        "residuals": residuals,
        "SS_res":    SS_res,
    }

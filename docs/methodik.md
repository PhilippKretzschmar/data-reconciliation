# Methodik: Lineare stationäre Datenrekonziliation

## Problem

Für N gemessene Ströme $x_i$ mit wahren Werten $x_i^*$:

$$x_i = x_i^* + \varepsilon_i, \quad \varepsilon_i \sim \mathcal{N}(0, \sigma_i^2)$$

mit $\sigma_i = \rho_i \cdot \bar{x}_i$ (relative Unsicherheit).

## Optimierungsproblem

$$\min_{\hat{x}} (\hat{x} - x)^\top Q^{-1} (\hat{x} - x) \quad \text{s.t.} \quad A\hat{x} = 0$$

mit $Q = \text{diag}(\sigma_1^2, \ldots, \sigma_N^2)$.

## Analytische Lösung

$$\hat{x} = x - QA^\top(AQA^\top + \lambda I)^{-1}Ax$$

## Quellen

- Narasimhan & Jordache (2000): *Data Reconciliation & Gross Error Detection*

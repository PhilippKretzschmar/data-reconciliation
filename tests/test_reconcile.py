"""Tests für reconciliation/reconcile.py"""
import numpy as np
import pytest
from data_reconciliation.reconciliation.reconcile import reconcile

np.random.seed(42)

A   = np.array([[1, 1, 1, -1, -1]], dtype=float)
rho = np.array([0.02, 0.05, 0.02, 0.02, 0.05])
mu  = np.array([1000, 20, 10000, 11010, 10], dtype=float)
X   = np.random.normal(mu, rho * mu, size=(100, 5))


def test_reconcile_output_keys():
    result = reconcile(X, A, rho)
    assert all(k in result for k in ["X_rec", "delta_X", "residuals", "SS_res"])


def test_reconcile_balance_closed():
    result = reconcile(X, A, rho)
    # Bilanzfehler nach DR sollte sehr klein sein
    max_residual = np.abs(result["residuals"]).max()
    assert max_residual < 1e-6, f"Bilanz nicht geschlossen: {max_residual}"


def test_reconcile_shapes():
    result = reconcile(X, A, rho)
    assert result["X_rec"].shape   == X.shape
    assert result["delta_X"].shape == X.shape
    assert result["SS_res"].shape  == (X.shape[0],)


def test_reconcile_regularization():
    result = reconcile(X, A, rho, lam=1.0)
    # Mit Regularisierung: Korrekturen kleiner, Residuale etwas größer als 0
    result_0 = reconcile(X, A, rho, lam=0.0)
    delta_lam = np.abs(result["delta_X"]).mean()
    delta_0   = np.abs(result_0["delta_X"]).mean()
    assert delta_lam <= delta_0 + 1e-6

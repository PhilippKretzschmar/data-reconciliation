"""Tests für preprocessing/filter.py"""
import numpy as np
import pytest
from data_reconciliation.preprocessing.filter import (
    IQRFilter, ResidualFilter, CompositeFilter
)

np.random.seed(0)
X_clean = np.random.normal(loc=[1000, 20, 10000], scale=[20, 1, 200], size=(500, 3))
A = np.array([[1, 1, -1]])   # vereinfachte Bilanz

# Ausreißer einfügen
X_outlier = X_clean.copy()
X_outlier[10, 0] = 5000   # extremer Ausreißer in Strom 0


def test_iqr_filter_clean():
    mask = IQRFilter(k=1.5).fit_transform(X_clean)
    assert mask.mean() > 0.9, "Zu viele saubere Punkte entfernt"


def test_iqr_filter_removes_outlier():
    mask = IQRFilter(k=1.5).fit_transform(X_outlier)
    assert not mask[10], "Ausreißer wurde nicht erkannt"


def test_residual_filter_clean():
    mask = ResidualFilter(A, threshold=3.0).fit_transform(X_clean)
    assert mask.mean() > 0.9


def test_composite_and():
    f    = CompositeFilter([IQRFilter(k=1.5), ResidualFilter(A)], mode="and")
    mask = f.fit_transform(X_outlier)
    assert not mask[10]


def test_composite_detailed_keys():
    f       = CompositeFilter([IQRFilter(), ResidualFilter(A)], mode="and")
    f.fit(X_clean)
    details = f.transform_detailed(X_clean)
    assert "IQRFilter"      in details
    assert "ResidualFilter" in details
    assert "combined"       in details

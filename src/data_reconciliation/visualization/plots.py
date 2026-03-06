"""
visualization/plots.py

Visualisierungsfunktionen für Roh- und rekonziliierte Daten.
"""

import numpy as np
import matplotlib.pyplot as plt


def plot_raw_data(X: np.ndarray, stream_ids: list,
                  mask: np.ndarray | None = None,
                  figsize: tuple = (14, 5)) -> plt.Figure:
    """
    1×2 Multiplot der Rohdaten:
        Links:  Zeitverlauf aller Ströme (optional: entfernte Punkte markiert)
        Rechts: Boxplot aller Ströme (normiert auf Mittelwert)

    Args:
        X:          (k, N) Rohdaten
        stream_ids: Liste der Strom-Nummern
        mask:       (k,) bool – stationäre Zeitschritte (optional)
        figsize:    Figurengröße
    """
    labels = [f"S{sid}" for sid in stream_ids]
    t      = np.arange(X.shape[0])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Zeitverlauf
    for i, label in enumerate(labels):
        ax1.plot(t, X[:, i], alpha=0.5, linewidth=0.5, label=label)
    if mask is not None:
        removed = ~mask
        ax1.scatter(t[removed], X[removed, 0] * np.nan,
                    color="red", s=5, zorder=5, label="entfernt (Filter)")
        for i in range(X.shape[1]):
            ax1.scatter(t[removed], X[removed, i],
                        color="red", s=3, alpha=0.4, zorder=5)

    ax1.set_xlabel("Zeitschritt t [h]")
    ax1.set_ylabel("Massenstrom [kg/h]")
    ax1.set_title("Rohdaten – Zeitverlauf")
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    # Boxplot (normiert)
    X_norm = X / X.mean(axis=0)
    ax2.boxplot(X_norm, labels=labels, showfliers=True,
                flierprops=dict(marker=".", markersize=2, alpha=0.3))
    ax2.axhline(1.0, color="red", linestyle="--", alpha=0.5, linewidth=1)
    ax2.set_ylabel("Normierter Massenstrom (x / x̄)")
    ax2.set_title("Rohdaten – Boxplot (normiert)")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_corrections(X: np.ndarray, X_rec: np.ndarray,
                     stream_ids: list,
                     figsize: tuple = (14, 5)) -> plt.Figure:
    """
    Vergleich Roh- vs. rekonziliierte Daten für jeden Strom.

    Args:
        X:          (k, N) Rohdaten
        X_rec:      (k, N) rekonziliierte Werte
        stream_ids: Liste der Strom-Nummern
    """
    N      = X.shape[1]
    labels = [f"S{sid}" for sid in stream_ids]
    fig, axes = plt.subplots(1, N, figsize=figsize, sharey=False)
    if N == 1:
        axes = [axes]

    for i, (ax, label) in enumerate(zip(axes, labels)):
        delta = X_rec[:, i] - X[:, i]
        ax.hist(delta, bins=50, color="steelblue", edgecolor="none", alpha=0.8)
        ax.axvline(0, color="red", linewidth=1, linestyle="--")
        ax.axvline(delta.mean(), color="orange", linewidth=1,
                   linestyle="--", label=f"Ø {delta.mean():.1f}")
        ax.set_title(label)
        ax.set_xlabel("Korrektur Δx [kg/h]")
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Häufigkeit")
    fig.suptitle("Verteilung der Rekonziliations-Korrekturen je Strom",
                 fontsize=11)
    plt.tight_layout()
    return fig

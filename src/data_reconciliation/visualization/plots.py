"""
visualization/plots.py

Visualisierungsfunktionen für Roh- und rekonziliierte Daten.
"""

import numpy as np
import matplotlib.pyplot as plt

# Schriftgrößen – zentral anpassbar
_FS       = 12   # Achsenbeschriftungen, Tick-Labels
_FS_TITLE = 13   # Subplot-Titel
_FS_SUP   = 13   # Suptitle
_FS_LEG   = 10   # Legende


# ---------------------------------------------------------------------------
# Hilfsfunktion
# ---------------------------------------------------------------------------

def _make_labels(stream_ids: list, stream_labels: dict | None) -> list[str]:
    """
    Erzeugt Beschriftungsliste aus stream_labels oder Fallback 'S{id}'.

    stream_labels erwartet: {int: {"klarname": str, ...}}
    """
    if stream_labels is None:
        return [f"S{sid}" for sid in stream_ids]
    return [
        stream_labels.get(sid, {}).get("klarname", f"S{sid}")
        for sid in stream_ids
    ]


# ---------------------------------------------------------------------------
# Plot 1: Rohdaten
# ---------------------------------------------------------------------------

def plot_raw_data(X: np.ndarray,
                  stream_ids: list,
                  mask: np.ndarray | None = None,
                  figsize: tuple = (14, 5),
                  stream_labels: dict | None = None) -> plt.Figure:
    """
    1×2 Multiplot der Rohdaten:
        Links:  Zeitverlauf aller Ströme (optional: entfernte Punkte markiert)
        Rechts: Boxplot aller Ströme (normiert auf Mittelwert)

    Args:
        X:              (k, N) Rohdaten
        stream_ids:     Liste der Strom-Nummern
        mask:           (k,) bool – stationäre Zeitschritte (optional)
        figsize:        Figurengröße
        stream_labels:  dict {int: {"klarname": str, ...}} (optional)
    """
    labels = _make_labels(stream_ids, stream_labels)
    t      = np.arange(X.shape[0])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # --- Links: Zeitverlauf ---
    for i, label in enumerate(labels):
        ax1.plot(t, X[:, i], alpha=0.5, linewidth=0.5, label=label)
    if mask is not None:
        removed = ~mask
        ax1.scatter(t[removed], X[removed, 0] * np.nan,
                    color="red", s=5, zorder=5, label="entfernt (Filter)")
        for i in range(X.shape[1]):
            ax1.scatter(t[removed], X[removed, i],
                        color="red", s=3, alpha=0.4, zorder=5)

    ax1.set_xlabel("Zeitschritt t [h]", fontsize=_FS)
    ax1.set_ylabel("Massenstrom [kg/h]", fontsize=_FS)
    ax1.set_title("Rohdaten – Zeitverlauf", fontsize=_FS_TITLE)
    ax1.tick_params(labelsize=_FS)
    ax1.legend(fontsize=_FS_LEG)
    ax1.grid(True, alpha=0.3)

    # --- Rechts: Boxplot (normiert) ---
    X_norm = X / X.mean(axis=0)
    ax2.boxplot(X_norm, labels=labels, showfliers=True,
            showmeans=True,
            meanprops=dict(marker="x", markeredgecolor="red",
                           markerfacecolor="red", markersize=8,
                           markeredgewidth=1.5),
            flierprops=dict(marker=".", markersize=2, alpha=0.3))
    ax2.set_xticklabels(labels, rotation=30, ha="right", fontsize=_FS)
    ax2.axhline(1.0, color="red", linestyle="--", alpha=0.5, linewidth=1)
    ax2.set_ylabel("Normierter Massenstrom (x / x̄)", fontsize=_FS)
    ax2.set_title("Rohdaten – Boxplot (normiert)", fontsize=_FS_TITLE)
    ax2.tick_params(axis="y", labelsize=_FS)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Plot 2: Rekonziliations-Korrekturen
# ---------------------------------------------------------------------------

def plot_corrections(X: np.ndarray,
                     X_rec: np.ndarray,
                     stream_ids: list,
                     figsize: tuple = (14, 5),
                     stream_labels: dict | None = None) -> plt.Figure:
    """
    Histogramm der Rekonziliations-Korrekturen je Strom.

    Args:
        X:              (k, N) Rohdaten
        X_rec:          (k, N) rekonziliierte Werte
        stream_ids:     Liste der Strom-Nummern
        figsize:        Figurengröße
        stream_labels:  dict {int: {"klarname": str, ...}} (optional)
    """
    N      = X.shape[1]
    labels = _make_labels(stream_ids, stream_labels)

    fig, axes = plt.subplots(1, N, figsize=figsize, sharey=False)
    if N == 1:
        axes = [axes]

    for i, (ax, label) in enumerate(zip(axes, labels)):
        delta = X_rec[:, i] - X[:, i]
        ax.hist(delta, bins=50, color="steelblue", edgecolor="none", alpha=0.8)
        ax.axvline(0, color="red", linewidth=1, linestyle="--")
        ax.axvline(delta.mean(), color="orange", linewidth=1,
                   linestyle="--", label=f"Ø {delta.mean():.1f}")
        ax.set_title(label, fontsize=_FS_TITLE)
        ax.set_xlabel("Korrektur Δx [kg/h]", fontsize=_FS)
        ax.tick_params(labelsize=_FS)
        ax.legend(fontsize=_FS_LEG)
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Häufigkeit", fontsize=_FS)
    fig.suptitle("Verteilung der Rekonziliations-Korrekturen je Strom",
                 fontsize=_FS_SUP)
    plt.tight_layout()
    return fig
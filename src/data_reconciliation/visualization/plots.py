"""
visualization/plots.py

Generische Visualisierungsfunktionen für Zeitreihen und Rekonziliationsergebnisse.
Einsetzbar für beliebige Zeitreihendaten, z.B. Massenströme, Residuale, etc.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter

# Schriftgrößen – zentral anpassbar
_FS       = 12   # Achsenbeschriftungen, Tick-Labels
_FS_TITLE = 13   # Subplot-Titel
_FS_SUP   = 13   # Suptitle
_FS_LEG   = 10   # Legende


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _make_labels(n: int,
                 labels: list[str] | None,
                 ids: list | None) -> list[str]:
    """
    Erzeugt eine Liste von n Beschriftungen nach folgender Priorität:

        1. labels direkt (beliebige Strings, z.B. Klarnamen) – kein S-Präfix
        2. ids mit "S"-Präfix  (nur wenn labels=None)
        3. Fallback: "0", "1", ... (wenn beides None)

    Args:
        n:       Anzahl benötigter Labels (= X.shape[1])
        labels:  Direkte Beschriftungsliste, z.B. ["Gesamtbilanz", "Reaktor"].
                 Hat Vorrang vor ids.
        ids:     Numerische IDs, werden zu "S4", "S16" etc. expandiert.
                 Nur verwendet wenn labels=None.
    """
    if labels is not None:
        return list(labels)[:n]
    if ids is not None:
        return [f"S{sid}" for sid in ids[:n]]
    return [str(i) for i in range(n)]


def _safe_normalize(X: np.ndarray) -> np.ndarray:
    """
    Normiert spaltenweise auf den Mittelwert (x / x̄).
    Spalten mit |x̄| < 1e-10 werden nicht normiert (Schutz vor Division durch Null,
    z.B. bei Residualen mit Mittelwert nahe 0).
    """
    mean = X.mean(axis=0)
    safe_mean = np.where(np.abs(mean) < 1e-10, 1.0, mean)
    return X / safe_mean


# ---------------------------------------------------------------------------
# Plot 1: Zeitverlauf + Boxplot
# ---------------------------------------------------------------------------

def plot_timeseries(X: np.ndarray,
                    labels: list[str] | None = None,
                    ids: list | None = None,
                    mask: np.ndarray | None = None,
                    figsize: tuple = (14, 5),
                    title_left: str = "Zeitverlauf",
                    title_right: str = "Boxplot",
                    xlabel: str = "Zeitschritt t [h]",
                    ylabel_left: str = "Wert",
                    ylabel_right: str | None = None,
                    normalize: bool = False,
                    hline: float | None = None,
                    hline_label: str | None = None,
                    sci_left: bool = False,
                    sci_right: bool = False) -> plt.Figure:
    """
    1×2 Multiplot: Zeitverlauf (links) und Boxplot (rechts).

    Generisch einsetzbar für beliebige Zeitreihen (Massenströme, Residuale,
    etc.). Labels für Legende und Boxplot-Kategorien werden einheitlich aus
    `labels` oder `ids` abgeleitet.

    Mittelwertdarstellung im Boxplot:
        normalize=True  → horizontale Referenzlinie bei 1.0 (x / x̄ = 1),
                          kein rotes Kreuz (redundant bei Normierung)
        normalize=False → rotes Kreuz zeigt arithmetischen Mittelwert je Kategorie,
                          keine automatische hline (Mittelwert liegt kategorieabhängig)

    In beiden Fällen wird der Mittelwert in einer Boxplot-Legende beschriftet.
    Die hline kann in beiden Modi explizit gesetzt oder unterdrückt werden.

    Args:
        X:            (k, N) Zeitreihendaten
        labels:       Direkte Beschriftungsliste, z.B. ["Gesamtbilanz", "Reaktor"].
                      Hat Vorrang vor ids, kein "S"-Präfix. (optional)
        ids:          Numerische Strom-IDs → werden zu "S4", "S16" expandiert.
                      Nur verwendet wenn labels=None. (optional)
        mask:         (k,) bool-Array – markiert z.B. gefilterte Zeitschritte
                      als rote Punkte im Zeitverlauf. (optional)
        figsize:      Figurengröße in Zoll. Default: (14, 5)
        title_left:   Titel linker Subplot. Default: "Zeitverlauf"
        title_right:  Titel rechter Subplot. Default: "Boxplot"
        xlabel:       x-Achsenbeschriftung Zeitverlauf. Default: "Zeitschritt t [h]"
        ylabel_left:  y-Achsenbeschriftung Zeitverlauf. Default: "Wert"
        ylabel_right: y-Achsenbeschriftung Boxplot.
                      Default: "Normierter Wert (x / x̄)" wenn normalize=True,
                               "Wert" wenn normalize=False.
        normalize:    True  → Boxplot normiert auf Spaltenmittelwert (x / x̄),
                               hline bei 1.0, kein rotes Kreuz.
                      False → Boxplot mit Rohdaten, rotes Kreuz für Mittelwert,
                               keine automatische hline. Default.
        hline:        Horizontale Referenzlinie im Boxplot. (optional)
                      Default: 1.0 wenn normalize=True, None wenn normalize=False.
                      Explizit auf None setzen um Linie zu unterdrücken,
                      z.B. für Residuale auf 0.0 setzen.
        hline_label:  Beschriftung der Referenzlinie in der Boxplot-Legende.
                      Default: "Mittelwert" wenn normalize=True,
                               "Referenz"   wenn normalize=False.
                      Explizit setzen um den Default zu überschreiben,
                      z.B. hline_label="Nullreferenz" für Residuale.
        sci_left:     True → wissenschaftliche Notation (z.B. 1×10⁶) auf der
                      y-Achse des Zeitverlaufs. Erzwungen unabhängig von der
                      Größenordnung. Default: False.
        sci_right:    True → wissenschaftliche Notation auf der y-Achse des
                      Boxplots. Erzwungen unabhängig von der Größenordnung.
                      Default: False.

    Returns:
        matplotlib Figure

    Beispiele:
        # Massenströme mit Klarnamen, normiert
        stream_names = [stream_meta[sid]["klarname"] for sid in stream_ids]
        fig = plot_timeseries(X, labels=stream_names, normalize=True,
                              ylabel_left=r"Massenstrom / kg$\\cdot$h$^{-1}$")

        # Bilanzresiduale, unnormiert, Nullreferenz explizit gesetzt
        fig = plot_timeseries(residuals, labels=balance_labels,
                              title_left="Bilanzresiduale – Zeitverlauf",
                              ylabel_left=r"Residual / kg$\\cdot$h$^{-1}$",
                              hline=0.0, sci_left=True)
    """
    n       = X.shape[1]
    _labels = _make_labels(n, labels, ids)
    t       = np.arange(X.shape[0])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # --- Links: Zeitverlauf ---
    for i, label in enumerate(_labels):
        ax1.plot(t, X[:, i], alpha=0.5, linewidth=0.5, label=label)

    if mask is not None:
        removed = ~mask
        # Dummy-Scatter nur für Legendeneintrag
        ax1.scatter([], [], color="red", s=10, label="entfernt (Filter)")
        for i in range(n):
            ax1.scatter(t[removed], X[removed, i],
                        color="red", s=3, alpha=0.4, zorder=5)

    ax1.set_xlabel(xlabel, fontsize=_FS)
    ax1.set_ylabel(ylabel_left, fontsize=_FS)
    ax1.set_title(title_left, fontsize=_FS_TITLE)
    ax1.tick_params(labelsize=_FS)
    ax1.legend(fontsize=_FS_LEG)
    ax1.grid(True, alpha=0.3)

    if sci_left:
        fmt = ScalarFormatter(useMathText=True)
        fmt.set_scientific(True)
        fmt.set_powerlimits((0, 0))
        ax1.yaxis.set_major_formatter(fmt)

    # --- Rechts: Boxplot ---
    # normalize=True:  hline bei 1.0, kein rotes Kreuz (Mittelwert = 1 per Definition)
    # normalize=False: rotes Kreuz für Mittelwert, keine automatische hline
    X_box         = _safe_normalize(X) if normalize else X
    _ylabel_right = ylabel_right or ("Normierter Wert (x / x̄)" if normalize else "Wert")

    # hline: explizit übergeben > automatisch aus normalize > None
    if hline is not None:
        _hline = hline
    else:
        _hline = 1.0 if normalize else None

    ax2.boxplot(X_box, labels=_labels, showfliers=True,
                showmeans=not normalize,          # Kreuz nur im nicht-normierten Fall
                meanprops=dict(marker="x", markeredgecolor="red",
                               markerfacecolor="red", markersize=8,
                               markeredgewidth=1.5),
                flierprops=dict(marker=".", markersize=2, alpha=0.3))

    ax2.set_xticklabels(_labels, rotation=30, ha="right", fontsize=_FS)
    ax2.set_ylabel(_ylabel_right, fontsize=_FS)
    ax2.set_title(title_right, fontsize=_FS_TITLE)
    ax2.tick_params(axis="y", labelsize=_FS)
    ax2.grid(True, alpha=0.3)

    # Referenzlinie und Legende
    legend_handles = []
    if _hline is not None:
        _hline_label = hline_label or ("Mittelwert" if normalize else "Referenz")
        ax2.axhline(_hline, color="red", linestyle="--", alpha=0.7, linewidth=1)
        legend_handles.append(
            Line2D([0], [0], color="red", linestyle="--",
                   linewidth=1, label=_hline_label)
        )
    else:
        legend_handles.append(
            Line2D([0], [0], color="red", marker="x", linestyle="None",
                   markersize=8, markeredgewidth=1.5, label="Mittelwert")
        )
    ax2.legend(handles=legend_handles, fontsize=_FS_LEG)

    if sci_right:
        fmt = ScalarFormatter(useMathText=True)
        fmt.set_scientific(True)
        fmt.set_powerlimits((0, 0))
        ax2.yaxis.set_major_formatter(fmt)

    plt.tight_layout()
    return fig


# Rückwärtskompatibilität: alter Name bleibt verfügbar
plot_raw_data = plot_timeseries


# ---------------------------------------------------------------------------
# Plot 2: Rekonziliations-Korrekturen
# ---------------------------------------------------------------------------

def plot_corrections(X: np.ndarray,
                     X_rec: np.ndarray,
                     labels: list[str] | None = None,
                     ids: list | None = None,
                     figsize: tuple = (14, 5)) -> plt.Figure:
    """
    Histogramm der Rekonziliations-Korrekturen je Strom/Variable.

    Args:
        X:       (k, N) Rohdaten (vor Rekonziliation)
        X_rec:   (k, N) rekonziliierte Werte
        labels:  Direkte Beschriftungsliste, z.B. Klarnamen. (optional)
                 Hat Vorrang vor ids, kein "S"-Präfix.
        ids:     Numerische Strom-IDs → "S4", "S16" etc. (optional)
                 Nur verwendet wenn labels=None.
        figsize: Figurengröße in Zoll. Default: (14, 5)

    Returns:
        matplotlib Figure
    """
    N       = X.shape[1]
    _labels = _make_labels(N, labels, ids)

    fig, axes = plt.subplots(1, N, figsize=figsize, sharey=False)
    if N == 1:
        axes = [axes]

    for i, (ax, label) in enumerate(zip(axes, _labels)):
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
"""
visualization/save.py

Speicherfunktion für Matplotlib-Figures, unabhängig von der Plot-Erstellung.

Verwendung im Notebook:
    from data_reconciliation.visualization.plots import plot_raw_data
    from data_reconciliation.visualization.save import save_figure

    fig = plot_raw_data(X, stream_ids, mask=mask)
    save_figure(fig)
"""

import glob
import os
import re
from datetime import datetime

import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

_IMAGE_EXTENSIONS = ("*.png", "*.jpg", "*.jpeg", "*.bmp",
                     "*.tif", "*.tiff", "*.svg", "*.emf")

_SAVE_KWARGS = dict(
    dpi=150,
    bbox_inches="tight",
    format="png",
)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _extract_title(fig: plt.Figure) -> str:
    """
    Ermittelt einen Titel aus der Figure:
      1. Figure-Suptitle
      2. Titel des ersten Axes-Objekts
      3. Fallback: 'figure'
    """
    # Suptitle (wird von plt.suptitle() gesetzt)
    suptitle = fig._suptitle  # type: ignore[attr-defined]
    if suptitle is not None and suptitle.get_text().strip():
        return suptitle.get_text().strip()

    # Erstes Axes mit gesetztem Titel
    for ax in fig.get_axes():
        title = ax.get_title().strip()
        if title:
            return title

    return "figure"


def _sanitize(text: str) -> str:
    """Konvertiert einen Titelstring in einen dateisystemsicheren Namen."""
    text = text.lower()
    text = re.sub(r"[äöüÄÖÜ]", lambda m: {"ä":"ae","ö":"oe","ü":"ue",
                                            "Ä":"ae","Ö":"oe","Ü":"ue"}[m.group()], text)
    text = re.sub(r"ß", "ss", text)
    text = re.sub(r"[^\w\s-]", "", text)       # Sonderzeichen entfernen
    text = re.sub(r"[\s_]+", "_", text).strip("_")
    return text[:60]                            # Länge begrenzen


def _find_or_create_dir(subfolder: str) -> str:
    """
    Sucht `subfolder` unter docs/ oder files/ relativ zum aktuellen
    Arbeitsverzeichnis (CWD, typischerweise Projektwurzel im Notebook).
    Legt den Ordner an, falls er noch nicht existiert.

    Bevorzugung: docs/ > files/
    """
    cwd = os.getcwd()
    for base in ("docs", "files"):
        candidate = os.path.join(cwd, base, subfolder)
        if os.path.isdir(candidate):
            return candidate

    # Noch nicht vorhanden → unter docs/ anlegen
    target = os.path.join(cwd, "docs", subfolder)
    os.makedirs(target, exist_ok=True)
    return target


def _clear_images(directory: str) -> int:
    """Löscht alle Bild-Dateien im Verzeichnis. Gibt Anzahl zurück."""
    removed = 0
    for pattern in _IMAGE_EXTENSIONS:
        for f in glob.glob(os.path.join(directory, pattern)):
            os.remove(f)
            removed += 1
    return removed


# ---------------------------------------------------------------------------
# Öffentliche Funktion
# ---------------------------------------------------------------------------

def save_figure(
    fig: plt.Figure,
    subfolder: str = "plots",
    clear_existing: bool = False,
    verbose: bool = True,
) -> str:
    """
    Speichert eine Matplotlib-Figure als PNG in docs/<subfolder>/.

    Der Dateiname wird automatisch aus dem Figure-/Subplot-Titel und dem
    aktuellen Datum gebildet: ``YYYY-MM-DD_<titel>.png``

    Args:
        fig:            Matplotlib Figure-Objekt
        subfolder:      Unterordnername unterhalb von docs/ oder files/
                        (wird ggf. neu angelegt)
        clear_existing: Vorhandene Bilddateien im Zielordner vorher löschen
        verbose:        Pfad nach dem Speichern ausgeben

    Returns:
        Absoluter Pfad der gespeicherten Datei
    """
    target_dir = _find_or_create_dir(subfolder)

    if clear_existing:
        n = _clear_images(target_dir)
        if verbose and n:
            print(f"  {n} vorhandene Bilddatei(en) gelöscht: {target_dir}")

    title    = _extract_title(fig)
    stem = f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}_{_sanitize(title)}"
    filepath = os.path.join(target_dir, f"{stem}.png")

    fig.savefig(filepath, **_SAVE_KWARGS)

    if verbose:
        size_kb = os.path.getsize(filepath) / 1024
        print(f"  Gespeichert: {filepath}  ({size_kb:.0f} KB)")

    return filepath
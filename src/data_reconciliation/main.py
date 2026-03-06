"""
main.py

Pipeline-Orchestrierung für die Datenrekonziliation.

Verwendung:
    python -m data_reconciliation.main --input data/demo-daten.xlsx
    python -m data_reconciliation.main --input data/demo-daten.xlsx --lam 0.01
    python -m data_reconciliation.main --input data/demo-daten.xlsx --no-filter
"""

import argparse
import numpy as np

from data_reconciliation.io.reader import read_excel
from data_reconciliation.preprocessing.filter import (
    IQRFilter, ResidualFilter, CompositeFilter, filter_report
)
from data_reconciliation.reconciliation.reconcile import reconcile
from data_reconciliation.visualization.plots import (
    plot_raw_data, plot_corrections
)


def run(input_path: str,
        lam: float = 0.0,
        use_filter: bool = True,
        iqr_k: float = 1.5,
        residual_threshold: float = 3.0,
        output_dir: str = "files") -> dict:
    """
    Führt die vollständige DR-Pipeline aus.

    Args:
        input_path:          Pfad zur Excel-Datei
        lam:                 Regularisierungsparameter
        use_filter:          Instationaritäts-Filterung ein/aus
        iqr_k:               Tukey-Multiplikator für IQRFilter
        residual_threshold:  Schwellwert für ResidualFilter
        output_dir:          Verzeichnis für Plots und Ergebnisse

    Returns:
        dict mit X, X_rec, delta_X, residuals, SS_res, mask
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    # (a) Einlesen
    print("\n[1/4] Daten einlesen...")
    data = read_excel(input_path)
    X, A, rho = data["X"], data["A"], data["rho"]
    stream_ids = data["stream_ids"]
    print(f"      X: {X.shape}  A: {A.shape}  rho: {rho}")

    # (b) Filterung
    mask = np.ones(len(X), dtype=bool)
    if use_filter:
        print("\n[2/4] Instationaritäten filtern...")
        f = CompositeFilter([
                IQRFilter(k=iqr_k),
                ResidualFilter(A, threshold=residual_threshold)
            ], mode="and")
        detailed = f.fit(X).transform_detailed(X)
        mask     = detailed["combined"]
        filter_report(mask, detailed)
    else:
        print("\n[2/4] Filterung übersprungen (--no-filter).")

    X_stat = X[mask]

    # (c) Rekonziliation
    print("\n[3/4] Rekonziliation...")
    result = reconcile(X_stat, A, rho, lam=lam)
    print(f"      Mittlerer SS_res: {result['SS_res'].mean():.4f}")
    print(f"      Max.  SS_res:     {result['SS_res'].max():.4f}")

    # (d) Visualisierung
    print("\n[4/4] Visualisierung speichern...")
    fig1 = plot_raw_data(X, stream_ids, mask=mask)
    fig1.savefig(f"{output_dir}/rohdaten.png", dpi=150)

    fig2 = plot_corrections(X_stat, result["X_rec"], stream_ids)
    fig2.savefig(f"{output_dir}/korrekturen.png", dpi=150)

    print(f"      Plots gespeichert in: {output_dir}/")
    print("\n✓ Pipeline abgeschlossen.\n")

    return {**result, "mask": mask, "X_raw": X,
            "stream_ids": stream_ids}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Datenrekonziliation für Prozessdaten"
    )
    parser.add_argument("--input",  default="data/demo-daten.xlsx",
                        help="Pfad zur Excel-Eingabedatei")
    parser.add_argument("--lam",    type=float, default=0.0,
                        help="Regularisierungsparameter (Standard: 0.0)")
    parser.add_argument("--iqr-k", type=float, default=1.5,
                        help="Tukey-Multiplikator für IQRFilter (Standard: 1.5)")
    parser.add_argument("--threshold", type=float, default=3.0,
                        help="Schwellwert für ResidualFilter (Standard: 3.0)")
    parser.add_argument("--no-filter", action="store_true",
                        help="Instationaritäts-Filterung deaktivieren")
    parser.add_argument("--output", default="files",
                        help="Ausgabeverzeichnis (Standard: files/)")
    args = parser.parse_args()

    run(
        input_path=args.input,
        lam=args.lam,
        use_filter=not args.no_filter,
        iqr_k=args.iqr_k,
        residual_threshold=args.threshold,
        output_dir=args.output,
    )

# data-reconciliation

Modulares Python-Tool für lineare stationäre Datenrekonziliation
von Prozessdaten in der chemischen Prozessindustrie.

## Setup

```bash
conda env create -f environment.yml
conda activate data-reconciliation
pip install -e .
```

## Verwendung

```bash
python -m data_reconciliation.main --input data/demo-daten.xlsx
```

Optionale Argumente:
```
--lam 0.01          Regularisierungsparameter
--iqr-k 1.5         Tukey-Multiplikator für IQR-Filter
--threshold 3.0     Schwellwert für Residual-Filter
--no-filter         Filterung deaktivieren
--output files/     Ausgabeverzeichnis
```

## Tests

```bash
pytest tests/ -v
```

## Projektstruktur

```
data-reconciliation/
├── data/                          # Rohdaten (Excel-Input)
├── docs/                          # Dokumentation
├── files/                         # Outputs (Plots, Ergebnisse)
├── src/
│   └── data_reconciliation/
│       ├── io/reader.py           # Excel einlesen
│       ├── preprocessing/filter.py # Instationaritäts-Filterung
│       ├── reconciliation/reconcile.py
│       ├── visualization/plots.py
│       └── main.py
└── tests/
```

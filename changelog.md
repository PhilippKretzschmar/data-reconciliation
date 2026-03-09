Changelog


Alle relevanten Änderungen am Projekt werden hier dokumentiert. Format angelehnt an Keep a Changelog.


## [2026-03-09] – Visualisierung: Speicherfunktion und Plot-Verbesserungen

### Hinzugefügt
* `visualization/save.py`: Neue, von `plots.py` entkoppelte Speicherfunktion `save_figure(fig)`
  * Speichert Matplotlib-Figures als PNG in `docs/plots/` (Ordner wird ggf. angelegt)
  * Dateiname automatisch aus Figure-/Subplot-Titel + ISO-Datum: `YYYY-MM-DD_<titel>.png`
  * Optionales Löschen vorhandener Bilddateien vor dem Speichern (`clear_existing=True`)
  * Speicherparameter: `dpi=150`, `bbox_inches="tight"` (geeignet für Word- und PDF-Einbindung)
* Jupyter Shell Script Start/stop

### Geändert
* `visualization/plots.py`:
  * Schriftgrößen-Konstanten `_FS`, `_FS_TITLE`, `_FS_SUP`, `_FS_LEG` zentral oben im Modul definiert (alle auf 12/13/10 pt angehoben)
  * Hilfsfunktion `_make_labels()` ergänzt: Klarnamen aus `stream_labels`-Dict mit Fallback auf `S{id}`
  * Parameter `stream_labels: dict | None = None` in `plot_raw_data()` und `plot_corrections()` ergänzt
  * Boxplot (Rohdaten): x-Tick-Beschriftungen angewinkelt (`rotation=30, ha="right"`)
  * Boxplot (Rohdaten): Arithmetischer Mittelwert als rotes Kreuz ergänzt (`showmeans=True`)

### Behoben
* `visualization/save.py`: Parameter `optimize=True` aus `_SAVE_KWARGS` entfernt –
  wird von `FigureCanvasAgg.print_png()` nicht unterstützt und verursachte `TypeError`




[2026-03-06] – Projektinitialisierung

Hinzugefügt


Projektstruktur via setup_project.py angelegt (src/, tests/, docs/, notebooks/, data/, files/)



environment.yml für conda-Umgebung data-reconciliation (Python 3.11)



pyproject.toml und requirements.txt für Package-Installation



Demo-Daten data/demo-daten.xlsx erstellt (k=3000 Zeitschritte, N=5 Ströme: S4, S5, S16, S14, S12)





Zufälliges Rauschen: σ = ρ · x̄ je Strom



Systematischer Fehler: S16 +1.5% (simulierte Fehlkalibrierung)



Instationarität: Rampe auf S14 (+500 kg/h) und S12 (+200 kg/h) in den letzten 300 Stunden



io/reader.py: Einlesen von Stromdaten und Matrix A aus Excel



preprocessing/filter.py: IQRFilter, ResidualFilter, CompositeFilter



reconciliation/reconcile.py: Matrixbasierte lineare stationäre DR mit optionaler Tikhonov-Regularisierung



visualization/plots.py: Zeitverlauf und Boxplot der Rohdaten, Histogramm der Korrekturen



main.py: Pipeline-Orchestrierung mit CLI-Interface



Unit-Tests für reader, filter und reconcile (tests/)



docs/methodik.md: Mathematische Herleitung des Rekonziliationsproblems



Jupyter-Umgebung eingerichtet (JupyterLab via Anaconda Navigator)

Behoben





pyproject.toml: Build-Backend korrigiert (setuptools.backends.legacy:build → setuptools.build_meta)



io/reader.py: Stream-ID Parsing robuster gemacht – akzeptiert jetzt "S4", "S16" sowie 4, 16



preprocessing/filter.py: Unicode-Box-Zeichen ─ (U+2500) in filter_report entfernt (verursachte SyntaxError in Jupyter)

Entscheidungen





data/ und files/ in .gitignore – keine Rohdaten oder generierten Outputs ins Repo



Notebooks in notebooks/ Unterordner, Pfade mit Path().resolve().parent



Matrix-Operationen simultan über alle k Zeitschritte (CUDA-kompatibel via numpy/cupy Austausch)



CompositeFilter mit AND-Logik als Standard: IQRFilter (k=1.5) + ResidualFilter (threshold=3.0)

Offene Punkte / Nächste Schritte





[ ] Grobe Fehlerdetektion implementieren (Global Test, Measurement Test – Kap. 7 Narasimhan & Jordache)



[ ] Erstes Jupyter-Notebook in notebooks/ mit vollständiger Demo-Pipeline



[ ] Unit-Tests vervollständigen und pytest grün machen



[ ] Visualisierung der Rekonziliations-Ergebnisse erweitern




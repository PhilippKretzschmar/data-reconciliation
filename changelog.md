Changelog


Alle relevanten Änderungen am Projekt werden hier dokumentiert. Format angelehnt an Keep a Changelog.





## [2026-03-10] – Visualisierung: sci-Notation und Dokumentation
### Geändert
* `visualization/plots.py`: `plot_timeseries` um wissenschaftliche Notation erweitert
  * Neue Parameter `sci_left=False` / `sci_right=False`: aktivieren wissenschaftliche
    Achsenbeschriftung (z.B. 1×10⁶ statt 1000000) unabhängig für linken und rechten
    Subplot – sinnvoll bei sehr großen oder sehr kleinen Werten, funktioniert
    vorzeichenunabhängig (im Gegensatz zu Log-Skala)
  * `scilimits=(-3, 4)`: Notation wird nur bei Größenordnungen < 10⁻³ oder > 10⁴
    aktiviert, sonst Dezimaldarstellung
  * Docstring um Parameterbeschreibung und Verwendungsbeispiele ergänzt
  * Log-Skala bewusst nicht implementiert: bei vorzeichenbehafteten Daten
    (Residuale) konzeptionell ungeeignet
### Behoben
* `visualization/plots.py`: `sci_right` funktionierte nicht zuverlässig –
  `ticklabel_format()` durch expliziten `ScalarFormatter` ersetzt
  (`set_powerlimits((0, 0))` erzwingt sci-Notation unabhängig von der Größenordnung).
  Gilt analog für `sci_left`.




## [2026-03-10] – Visualisierung: Generalisierung plot_timeseries

### Geändert
* `visualization/plots.py`: `plot_raw_data` zu `plot_timeseries` umbenannt und vollständig generalisiert
  * Rückwärtskompatibilität erhalten: `plot_raw_data = plot_timeseries` als Alias
  * **Labels**: einheitliches Konzept über neue Hilfsfunktion `_make_labels(n, labels, ids)`:
    * `labels` (direkte Stringliste) hat Vorrang – kein "S"-Präfix
    * `ids` (numerische IDs) → "S4", "S16" etc. – nur wenn `labels=None`
    * Fallback: "0", "1", ... wenn beides `None`
  * `stream_labels`-Parameter entfernt – Klarnamen werden als `labels`-Liste direkt übergeben
  * **Neue Parameter**: `xlabel`, `hline` (Referenzlinie im Boxplot, abschaltbar)
  * `ylabel_left` Default von `"Massenstrom [kg/h]"` → `"Wert"` (domänenneutral)
  * `normalize=False` als neuer Default (vorher `True`) – sicherer für generische Nutzung
  * Neue Hilfsfunktion `_safe_normalize()`: Schutz vor Division durch Null bei Mittelwerten nahe 0
  * Darstellung gefilterter Punkte im Zeitverlauf korrigiert: Dummy-Scatter für Legendeneintrag
  * `plot_corrections`: Parameter `stream_labels` → `labels`/`ids` analog angepasst
  * Docstrings und Kommentare vollständig überarbeitet


## [2026-03-10] – Massenbilanz-Diagnose

### Hinzugefügt
* `reconciliation/balance.py`: Neue Funktion `compute_mass_balance(X, A, balance_ids=None)`
  * Berechnet den rohen Massenbilanz-Fehler **vor** der Rekonziliation: `R = X · A^T`
  * Rückgabe: `residuals (k, M)` – Bilanzfehler je Zeitschritt und Bilanzraum [kg/h]
  * Rückgabe: `residuals_mean (M,)` – Mittlerer Bilanzfehler je Bilanzraum über alle k Zeitschritte
  * Rückgabe: `balance_ids` – Bezeichnungen der Bilanzräume, unverändert durchgereicht (konsistent mit `reader.py`)
  * Funktion ist generalisierbar: ein Call je Input, kein interner Zustand
  * CUDA-kompatibel via `numpy`/`cupy`-Austausch (analog zu `reconcile.py`)
* `tests/test_balance.py`: Unit-Tests für `compute_mass_balance()`
  * Prüft Rückgabestruktur, Shapes, Rechenformel, systematischen Fehler,
    mehrere Bilanzräume sowie Unabhängigkeit zweier Calls mit verschiedenen Inputs
* Visualisierung: optionale Parameter title_left, title_right

### Geändert
* `main.py`:
  * Import von `compute_mass_balance` ergänzt
  * Zwei neue Pipeline-Schritte eingeführt:
    * **[2/5]** `balance_raw  = compute_mass_balance(X,      A, balance_ids)` – Rohdaten
    * **[4/5]** `balance_stat = compute_mass_balance(X_stat, A, balance_ids)` – gefilterte Daten
  * Mittlerer Bilanzfehler je Bilanzraum wird für beide Inputs auf der Konsole ausgegeben
  * Return-Dict um `balance_raw` und `balance_stat` erweitert
  * `stream_labels` wird nun konsistent an `plot_raw_data()` und `plot_corrections()` übergeben
  * Schritte neu nummeriert: [1–5] statt [1–4]
* grafik-Export: timestamp im Dateinamen, vorhandene Dateien werden per Default nicht gelöscht



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




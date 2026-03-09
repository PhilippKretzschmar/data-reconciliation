# =============================================================================
# start_jupyter.ps1
# -----------------------------------------------------------------------------
# Zweck:    Aktiviert die Conda-Umgebung "data-reconciliation" und startet
#           Jupyter Lab im Projektstamm-Verzeichnis.
#
# Nutzung:  Dieses Script im Projektstamm ablegen und in der PowerShell
#           mit folgendem Befehl aufrufen:
#               .\start_jupyter.ps1
#
# Hinweis:  Einmalig muss die Skriptausführung in PowerShell erlaubt werden:
#               Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# =============================================================================


# -----------------------------------------------------------------------------
# SCHRITT 1: Projektverzeichnis bestimmen
# -----------------------------------------------------------------------------
# Split-Path gibt den Ordner zurück, in dem dieses Script selbst liegt.
# Dadurch funktioniert das Script unabhängig davon, von welchem Verzeichnis
# aus es aufgerufen wird — solange es im Projektstamm liegt.
$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Name der Conda-Umgebung, exakt so wie in environment.yml definiert
$ENV_NAME = "data-reconciliation"


# -----------------------------------------------------------------------------
# SCHRITT 2: Ins Projektverzeichnis wechseln
# -----------------------------------------------------------------------------
# Jupyter Lab öffnet standardmäßig das Verzeichnis, aus dem es gestartet wird.
# Durch den Wechsel ins Projektverzeichnis landen wir direkt im richtigen Ordner.
Write-Host ""
Write-Host "Wechsle ins Projektverzeichnis:" -ForegroundColor Cyan
Write-Host "  $PROJECT_DIR" -ForegroundColor White
Set-Location $PROJECT_DIR


# -----------------------------------------------------------------------------
# SCHRITT 3: Conda für PowerShell initialisieren
# -----------------------------------------------------------------------------
# Conda ist in der PowerShell nicht automatisch verfügbar — es muss zuerst
# ein sogenannter "Hook" geladen werden. Dieser Hook registriert den Befehl
# "conda" in der aktuellen Shell-Session.
#
# Der Hook liegt typischerweise unter einem dieser Pfade:
#   - Anaconda:  %USERPROFILE%\anaconda3\shell\condabin\conda-hook.ps1
#   - Miniconda: %USERPROFILE%\miniconda3\shell\condabin\conda-hook.ps1
#
# Passe den Pfad hier an, falls deine Installation woanders liegt.
# Den korrekten Pfad findest du mit: where conda (in der Anaconda Prompt)

$condaHookAnaconda  = "$env:USERPROFILE\anaconda3\shell\condabin\conda-hook.ps1"
$condaHookMiniconda = "$env:USERPROFILE\miniconda3\shell\condabin\conda-hook.ps1"

Write-Host ""
Write-Host "Suche Conda-Installation..." -ForegroundColor Cyan

if (Test-Path $condaHookAnaconda) {
    # Anaconda-Installation gefunden
    Write-Host "  Anaconda gefunden. Lade Hook..." -ForegroundColor White
    & $condaHookAnaconda
}
elseif (Test-Path $condaHookMiniconda) {
    # Miniconda-Installation gefunden
    Write-Host "  Miniconda gefunden. Lade Hook..." -ForegroundColor White
    & $condaHookMiniconda
}
else {
    # Kein bekannter Pfad gefunden — Fehlermeldung und Abbruch
    Write-Host ""
    Write-Host "FEHLER: Conda-Installation nicht gefunden!" -ForegroundColor Red
    Write-Host "Bitte den Pfad zu conda-hook.ps1 manuell in diesem Script anpassen." -ForegroundColor Yellow
    Write-Host "Tipp: Den korrekten Pfad in der Anaconda Prompt mit 'where conda' ermitteln." -ForegroundColor Yellow
    exit 1  # Script mit Fehlercode beenden
}


# -----------------------------------------------------------------------------
# SCHRITT 4: Conda-Umgebung aktivieren
# -----------------------------------------------------------------------------
# Aktiviert die Umgebung "data-reconciliation". Danach zeigt die Shell
# das Präfix (data-reconciliation) an und alle Python-Befehle sowie
# Pakete beziehen sich auf diese Umgebung.
Write-Host ""
Write-Host "Aktiviere Conda-Umgebung: $ENV_NAME" -ForegroundColor Green
conda activate $ENV_NAME

# Prüfen ob die Aktivierung erfolgreich war
# $LASTEXITCODE ist 0 bei Erfolg, ungleich 0 bei Fehler
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "FEHLER: Umgebung '$ENV_NAME' konnte nicht aktiviert werden!" -ForegroundColor Red
    Write-Host "Tipp: Umgebung erstellen mit: conda env create -f environment.yml" -ForegroundColor Yellow
    exit 1
}


# -----------------------------------------------------------------------------
# SCHRITT 5: Jupyter Lab starten
# -----------------------------------------------------------------------------
# Startet Jupyter Lab mit dem Projektstamm als Wurzelverzeichnis.
# --notebook-dir legt fest, welchen Ordner Jupyter im Browser als oberste
# Ebene anzeigt — hier das Projektverzeichnis, damit alle Unterordner
# (notebooks/, data/, src/ etc.) direkt erreichbar sind.
#
# Jupyter öffnet automatisch einen Browser-Tab. Der Server läuft im
# Vordergrund dieses PowerShell-Fensters, bis er mit Ctrl+C gestoppt wird
# oder stop_jupyter.ps1 aufgerufen wird.
Write-Host ""
Write-Host "Starte Jupyter Lab..." -ForegroundColor Yellow
Write-Host "  Stammverzeichnis: $PROJECT_DIR" -ForegroundColor White
Write-Host ""
Write-Host "Zum Beenden: Ctrl+C in diesem Fenster oder stop_jupyter.ps1 aufrufen." -ForegroundColor DarkGray
Write-Host ""

jupyter lab --notebook-dir=$PROJECT_DIR
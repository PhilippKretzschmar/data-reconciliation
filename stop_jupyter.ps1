# =============================================================================
# stop_jupyter.ps1
# -----------------------------------------------------------------------------
# Zweck:    Beendet alle laufenden Jupyter-Server und -Prozesse sauber.
#
# Nutzung:  In einem neuen PowerShell-Fenster (oder Tab) aufrufen:
#               .\stop_jupyter.ps1
#
#           Alternativ kann Jupyter auch direkt im Start-Fenster mit
#           Ctrl+C beendet werden.
#
# Hinweis:  Das Script verwendet zwei Methoden zur Sicherheit:
#           1. Jupyter's eigene Stop-Befehle (sauber, speichert offene Dateien)
#           2. Windows-Prozess-Kill als Fallback (hart, sofortig)
# =============================================================================


# -----------------------------------------------------------------------------
# SCHRITT 1: Jupyter Server über eigene API sauber beenden
# -----------------------------------------------------------------------------
# "jupyter server stop --all" schickt einen regulären Shutdown-Befehl an alle
# laufenden Jupyter-Server. Das ist der bevorzugte Weg, da Jupyter dabei
# noch offene Notebooks speichern und Ressourcen freigeben kann.
#
# "2>$null" unterdrückt Fehlermeldungen (z.B. wenn kein Server läuft),
# damit die Ausgabe sauber bleibt.

Write-Host ""
Write-Host "Beende Jupyter-Server (sauberer Shutdown)..." -ForegroundColor Yellow

jupyter server stop --all   2>$null   # Jupyter Lab / Jupyter Server
jupyter notebook stop --all 2>$null   # Classic Notebook (Fallback, ältere Versionen)


# -----------------------------------------------------------------------------
# SCHRITT 2: Verbleibende Prozesse per Windows-Prozessmanager beenden
# -----------------------------------------------------------------------------
# Falls der saubere Shutdown nicht alle Prozesse beendet hat (z.B. bei
# hängenden Kernel-Prozessen), werden hier alle Prozesse mit "jupyter"
# im Namen gefunden und hart beendet.
#
# Get-Process -Name "jupyter*"  sucht alle Prozesse, deren Name mit
#   "jupyter" beginnt (z.B. jupyter-lab, jupyter-notebook, jupyter-kernel)
# -ErrorAction SilentlyContinue  verhindert eine Fehlermeldung, wenn
#   keine solchen Prozesse gefunden werden
# Stop-Process -Force  beendet den Prozess sofort ohne Rückfrage

Write-Host ""
Write-Host "Suche verbleibende Jupyter-Prozesse..." -ForegroundColor Cyan

$jupyterProcesses = Get-Process -Name "jupyter*" -ErrorAction SilentlyContinue

if ($jupyterProcesses) {
    # Mindestens ein Prozess wurde gefunden — jeden einzeln beenden und melden
    foreach ($proc in $jupyterProcesses) {
        Write-Host "  Beende Prozess: $($proc.Name)  (PID $($proc.Id))" -ForegroundColor White
        Stop-Process -Id $proc.Id -Force
    }
    Write-Host ""
    Write-Host "Alle Jupyter-Prozesse wurden beendet." -ForegroundColor Green
}
else {
    # Kein Prozess mehr aktiv — alles sauber
    Write-Host "  Keine laufenden Jupyter-Prozesse gefunden." -ForegroundColor DarkGray
}


# -----------------------------------------------------------------------------
# SCHRITT 3: Abschlussmeldung
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "Fertig. Jupyter wurde vollstaendig beendet." -ForegroundColor Green
Write-Host "Die Conda-Umgebung bleibt aktiv bis das PowerShell-Fenster geschlossen wird." -ForegroundColor DarkGray
Write-Host ""
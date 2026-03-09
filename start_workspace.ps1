# =============================================================================
# toggle_workspace.ps1
# -----------------------------------------------------------------------------
# Zweck:    Startet oder beendet die vollstaendige Arbeitsumgebung fuer
#           data-reconciliation – je nach aktuellem Zustand.
#
#           Erster Klick  -> Workspace hochfahren  (Jupyter, Zotero, Word, Claude)
#           Zweiter Klick -> Workspace herunterfahren
#
# Nutzung:  Verknuepfung auf dem Desktop oder in der Taskleiste anlegen:
#           powershell.exe -NoExit -ExecutionPolicy Bypass -File "...\toggle_workspace.ps1"
#
# Hinweis:  start_jupyter.ps1 und stop_jupyter.ps1 muessen im gleichen
#           Ordner liegen wie dieses Script.
# =============================================================================

# -----------------------------------------------------------------------------
# Konfiguration
# -----------------------------------------------------------------------------
$PROJECT_DIR  = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ZOTERO_EXE   = "C:\Program Files\Zotero\zotero.exe"
$WORD_EXE     = "C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"
$CLAUDE_APP   = "shell:AppsFolder\Claude_pzs8sxrjxfjjc!Claude"
$WORD_FILE    = ""   # Optional: z.B. "C:\Users\Admin\Desktop\bericht.docx"

# -----------------------------------------------------------------------------
# Hilfsfunktion
# -----------------------------------------------------------------------------
function Write-Line {
    Write-Host "  ---------------------------------------------" -ForegroundColor DarkGray
}

# -----------------------------------------------------------------------------
# Zustand pruefen
# -----------------------------------------------------------------------------
$jupyterLaeuft = Get-Process -Name "jupyter*" -ErrorAction SilentlyContinue
$zoteroLaeuft  = Get-Process -Name "zotero"   -ErrorAction SilentlyContinue
$wordLaeuft    = Get-Process -Name "WINWORD"   -ErrorAction SilentlyContinue
$claudeLaeuft  = Get-Process -Name "claude"    -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host "   Workspace Toggle - data-reconciliation"      -ForegroundColor Cyan
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Aktueller Zustand:" -ForegroundColor White
Write-Host "    Jupyter : $(if ($jupyterLaeuft) { 'laueft  [ON]' } else { 'gestoppt' })" -ForegroundColor $(if ($jupyterLaeuft) { 'Green' } else { 'DarkGray' })
Write-Host "    Zotero  : $(if ($zoteroLaeuft)  { 'laueft  [ON]' } else { 'gestoppt' })" -ForegroundColor $(if ($zoteroLaeuft)  { 'Green' } else { 'DarkGray' })
Write-Host "    Word    : $(if ($wordLaeuft)    { 'laueft  [ON]' } else { 'gestoppt' })" -ForegroundColor $(if ($wordLaeuft)    { 'Green' } else { 'DarkGray' })
Write-Host "    Claude  : $(if ($claudeLaeuft)  { 'laueft  [ON]' } else { 'gestoppt' })" -ForegroundColor $(if ($claudeLaeuft)  { 'Green' } else { 'DarkGray' })
Write-Host ""

# -----------------------------------------------------------------------------
# Starten oder Beenden
# -----------------------------------------------------------------------------
if ($jupyterLaeuft) {

    # HERUNTERFAHREN
    Write-Host "  Aktion: Workspace wird beendet..." -ForegroundColor Yellow
    Write-Host ""

    Write-Host "  [1/5] Jupyter beenden..." -ForegroundColor Cyan
    & "$PROJECT_DIR\stop_jupyter.ps1"
    Write-Line

    Write-Host "  [2/5] Zotero beenden..." -ForegroundColor Cyan
    if ($zoteroLaeuft) {
        Stop-Process -Name "zotero" -Force -ErrorAction SilentlyContinue
        Write-Host "        Zotero wurde beendet." -ForegroundColor Green
    } else {
        Write-Host "        Zotero lief nicht." -ForegroundColor DarkGray
    }
    Write-Line

    Write-Host "  [3/5] Word beenden..." -ForegroundColor Cyan
    if ($wordLaeuft) {
        Stop-Process -Name "WINWORD" -ErrorAction SilentlyContinue
        Write-Host "        Word wurde beendet." -ForegroundColor Green
        Write-Host "        Hinweis: Bitte Speicher-Rueckfragen manuell bestaetigen." -ForegroundColor DarkGray
    } else {
        Write-Host "        Word lief nicht." -ForegroundColor DarkGray
    }
    Write-Line

    Write-Host "  [4/5] Claude beenden..." -ForegroundColor Cyan
    if ($claudeLaeuft) {
        Stop-Process -Name "claude" -Force -ErrorAction SilentlyContinue
        Write-Host "        Claude wurde beendet." -ForegroundColor Green
    } else {
        Write-Host "        Claude lief nicht." -ForegroundColor DarkGray
    }
    Write-Line

    # Jupyter-Terminal-Fenster schliessen
    Write-Host "  Aufraeumen: Jupyter-Terminal schliessen..." -ForegroundColor Cyan
    $psWindows = Get-Process -Name "powershell" -ErrorAction SilentlyContinue |
                 Where-Object { $_.MainWindowTitle -like "*jupyter*" -or
                                $_.MainWindowTitle -like "*data-reconciliation*" }
    foreach ($pw in $psWindows) {
        Stop-Process -Id $pw.Id -Force -ErrorAction SilentlyContinue
    }

    Write-Host ""
    Write-Host "  Workspace wurde vollstaendig heruntergefahren." -ForegroundColor Green

} else {

    # HOCHFAHREN
    Write-Host "  Aktion: Workspace wird gestartet..." -ForegroundColor Yellow
    Write-Host ""

    Write-Host "  [1/5] Jupyter starten..." -ForegroundColor Cyan
    & "$PROJECT_DIR\start_jupyter.ps1"
    Write-Line

    Write-Host "  [2/5] Zotero starten..." -ForegroundColor Cyan
    if (-not $zoteroLaeuft) {
        if (Test-Path $ZOTERO_EXE) {
            Start-Process $ZOTERO_EXE
            Write-Host "        Zotero gestartet." -ForegroundColor Green
        } else {
            Write-Host "        WARNUNG: Zotero nicht gefunden unter: $ZOTERO_EXE" -ForegroundColor Yellow
        }
    } else {
        Write-Host "        Zotero laueft bereits." -ForegroundColor DarkGray
    }
    Write-Line

    Write-Host "  [3/5] Word starten..." -ForegroundColor Cyan
    if (-not $wordLaeuft) {
        if (Test-Path $WORD_EXE) {
            if ($WORD_FILE -ne "" -and (Test-Path $WORD_FILE)) {
                Start-Process $WORD_FILE
                Write-Host "        Word geoeffnet mit: $WORD_FILE" -ForegroundColor Green
            } else {
                Start-Process $WORD_EXE
                Write-Host "        Word gestartet." -ForegroundColor Green
            }
        } else {
            Write-Host "        WARNUNG: Word nicht gefunden unter: $WORD_EXE" -ForegroundColor Yellow
        }
    } else {
        Write-Host "        Word laueft bereits." -ForegroundColor DarkGray
    }
    Write-Line

    Write-Host "  [4/5] Claude starten..." -ForegroundColor Cyan
    if (-not $claudeLaeuft) {
        Start-Process $CLAUDE_APP
        Write-Host "        Claude gestartet." -ForegroundColor Green
    } else {
        Write-Host "        Claude laueft bereits." -ForegroundColor DarkGray
    }
    Write-Line

    Write-Host ""
    # Projektordner im Explorer oeffnen
    Write-Host "  [5/5] Projektordner oeffnen..." -ForegroundColor Cyan
    Start-Process "C:\Users\Admin\Nextcloud-RP\997_Python-Projekte\data-reconciliation"
    Write-Host "        Projektordner geoeffnet." -ForegroundColor Green
    Write-Line

    Write-Host "  Workspace wurde gestartet." -ForegroundColor Green
    Write-Host "  Erneuter Aufruf dieses Scripts beendet alles." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host ""
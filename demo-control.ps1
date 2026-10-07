# Kyanos demo control - run from the repo root.
#   ./demo-control.ps1 start            start the live PMS simulator (new bookings every ~6 s) in the background
#   ./demo-control.ps1 burst [N] [HOTEL] drop a tour-operator group block, e.g. ./demo-control.ps1 burst 25 KYN-OLY
#   ./demo-control.ps1 status           simulator rows in the PMS + process state
#   ./demo-control.ps1 stop             stop the simulator
#   ./demo-control.ps1 reset            stop + delete all simulator bookings (ConfirmationNo 'KL...')
#   ./demo-control.ps1 warmup           wake the capacity: refresh the semantic model and the lakehouse SQL endpoint metadata
param([string]$cmd = "status", [string]$a1 = "", [string]$a2 = "")
$root = $PSScriptRoot
$pidFile = Join-Path $root ".sim.pid"
$py = "python"

function Get-SimProcess {
    if (Test-Path $pidFile) {
        $p = Get-Process -Id (Get-Content $pidFile) -ErrorAction SilentlyContinue
        if ($p) { return $p }
    }
    return $null
}

switch ($cmd) {
    "start" {
        if (Get-SimProcess) { Write-Host "Simulator already running (PID $((Get-SimProcess).Id))"; break }
        $p = Start-Process -FilePath $py -ArgumentList "src\pms_live_sim.py", "run", "--every", "6" -WorkingDirectory $root `
             -RedirectStandardOutput (Join-Path $root "sim.log") -RedirectStandardError (Join-Path $root "sim.err.log") -WindowStyle Hidden -PassThru
        $p.Id | Set-Content $pidFile
        Write-Host "Live PMS simulator started (PID $($p.Id)). Follow it with: Get-Content sim.log -Wait"
    }
    "stop" {
        $p = Get-SimProcess
        if ($p) { Stop-Process -Id $p.Id; Remove-Item $pidFile -ErrorAction SilentlyContinue; Write-Host "Simulator stopped" } else { Write-Host "Simulator not running" }
    }
    "burst" {
        $n = if ($a1) { $a1 } else { "25" }; $h = if ($a2) { $a2 } else { "KYN-OLY" }
        & $py (Join-Path $root "src\pms_live_sim.py") burst $n $h
    }
    "status" {
        $p = Get-SimProcess
        Write-Host ("Simulator process: " + $(if ($p) { "running (PID $($p.Id))" } else { "stopped" }))
        & $py (Join-Path $root "src\pms_live_sim.py") status
    }
    "reset" {
        & $PSCommandPath stop
        & $py (Join-Path $root "src\pms_live_sim.py") reset
    }
    "warmup" {
        & $py (Join-Path $root "src\warmup.py")
    }
    default { Write-Host "usage: ./demo-control.ps1 start|burst [N] [HOTEL]|status|stop|reset|warmup" }
}

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root

try {
    python "scripts\generate_handbook.py"

    $runner = Join-Path $root "tmp\playwright-runner"
    $playwrightMarker = Join-Path $runner "node_modules\playwright"
    if (-not (Test-Path $playwrightMarker)) {
        New-Item -ItemType Directory -Force -Path $runner | Out-Null
        npm install playwright --prefix $runner | Out-Null
    }

    $env:NODE_PATH = (Resolve-Path (Join-Path $runner "node_modules")).Path
    node "scripts\render_pdf.js" "output\pdf\iccm_2026_handbook.html" "output\pdf\iccm_2026_handbook.pdf"
}
finally {
    Pop-Location
}

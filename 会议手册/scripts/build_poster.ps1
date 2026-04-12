$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root

try {
    $htmlPath = "output\pdf\iccm_2026_poster_a4.html"
    $pngPath = "output\pdf\iccm_2026_poster_a4.png"
    $pdfPath = "output\pdf\iccm_2026_poster_a4.pdf"
    $previewDir = "tmp\pdfs\poster_a4"
    $previewPrefix = Join-Path $previewDir "poster"

    python "scripts\generate_poster.py" --output-html $htmlPath

    $runner = Join-Path $root "tmp\playwright-runner"
    $playwrightMarker = Join-Path $runner "node_modules\playwright"
    if (-not (Test-Path $playwrightMarker)) {
        New-Item -ItemType Directory -Force -Path $runner | Out-Null
        npm install playwright --prefix $runner | Out-Null
    }

    $env:NODE_PATH = (Resolve-Path (Join-Path $runner "node_modules")).Path
    node "scripts\render_poster.js" $htmlPath $pngPath $pdfPath

    if (Get-Command pdftoppm -ErrorAction SilentlyContinue) {
        New-Item -ItemType Directory -Force -Path $previewDir | Out-Null
        pdftoppm -png $pdfPath $previewPrefix | Out-Null
    }
}
finally {
    Pop-Location
}

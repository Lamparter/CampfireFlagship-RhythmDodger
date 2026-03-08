param(
    [Parameter(Mandatory = $true)]
    [string]$SvgPath,

    [string]$OutputPath = ""
)

# Target canvas size
$canvasW = 790
$canvasH = 395

# Resolve paths
$SvgFull = (Resolve-Path $SvgPath).Path
if (-not $OutputPath) {
    $OutputPath = [IO.Path]::ChangeExtension($SvgFull, ".png")
}
$OutFull = (Resolve-Path (Split-Path $OutputPath -Parent) -ErrorAction SilentlyContinue)
if (-not $OutFull) {
    New-Item -ItemType Directory -Path (Split-Path $OutputPath -Parent) -Force | Out-Null
}
$OutFull = (Resolve-Path (Split-Path $OutputPath -Parent)).Path + "\" + (Split-Path $OutputPath -Leaf)

# Temporary full‑resolution render (keeps aspect ratio)
$tmp = [IO.Path]::GetTempFileName() + ".png"

# Step 1: Render SVG at max size while preserving aspect ratio
# We render to the *larger* of the two dimensions so it fills the box.
$scaleW = $canvasW
$scaleH = $canvasH

# Inkscape export
$inkArgs = @(
    "`"$SvgFull`"",
    "--export-type=png",
    "--export-filename=`"$tmp`"",
    "--export-width=$scaleW",
    "--export-height=$scaleH",
    "--export-background-opacity=0"
)

Start-Process -FilePath "C:\Program Files\Inkscape\bin\inkscape.exe" -ArgumentList $inkArgs -Wait -NoNewWindow

# Step 2: Composite onto a transparent 790×395 canvas (centered)
# Using ImageMagick for the compositing step
$magickArgs = @(
    "-size", "${canvasW}x${canvasH}",
    "canvas:none",
    "`"$tmp`"",
    "-gravity", "center",
    "-compose", "over",
    "-composite",
    "`"$OutFull`""
)

Start-Process -FilePath "magick" -ArgumentList $magickArgs -Wait -NoNewWindow

Remove-Item $tmp -Force

Write-Host "Done. Output saved to $OutFull"
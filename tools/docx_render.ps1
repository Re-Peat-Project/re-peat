# Finish a Word file built by project_report.py: update the fields (table of contents, page numbers) and embed the
# report fonts, so readers without Source Serif 4 / Source Sans 3 installed see the same page. Saves in place.
#   powershell -File re-peat/tools/docx_render.ps1 <in.docx> [<out.pdf>]
# A PDF is written only when <out.pdf> is given (for layout checks).
param([string]$In, [string]$Out = "")
$In = (Resolve-Path $In).Path
$w = New-Object -ComObject Word.Application
$w.Visible = $false
try {
    $d = $w.Documents.Open($In)
    $d.Fields.Update() | Out-Null
    foreach ($t in $d.TablesOfContents) { $t.Update() | Out-Null }
    $d.EmbedTrueTypeFonts = $true
    $d.SaveSubsetFonts = $false
    $d.Save()
    if ($Out) { $d.ExportAsFixedFormat($Out, 17) }
    $d.Close()
} finally { $w.Quit() }
Write-Output $In

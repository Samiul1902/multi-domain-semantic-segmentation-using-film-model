<#
    ReMedFiLM V9 -- DOCX -> PDF export (Word COM).

    Repairs two defects of export_v9_pdf.ps1:
      1. it wrote the PDF only into full_doc_report\V9\ instead of the main
         full_doc_report\ directory required for the final deliverable;
      2. it updated fields but never refreshed TOC page numbers after the
         final repagination pass.

    The source DOCX is never modified: Word opens a working copy, refreshes
    fields and the TOC, and exports from that copy.
#>
$ErrorActionPreference = 'Stop'

$root   = 'D:\Softfors\jup'
$fdr    = Join-Path $root 'full_doc_report'
$v9     = Join-Path $fdr  'V9'
$docx   = Join-Path $fdr  'ReMedFiLM_Complete_Scientific_Report_V9.docx'
$pdf    = Join-Path $fdr  'ReMedFiLM_Complete_Scientific_Report_V9.pdf'
$pdfV9  = Join-Path $v9   'ReMedFiLM_Complete_Scientific_Report_V9.pdf'
$work   = Join-Path $v9   'v9_build\.v9_final_word_work.docx'
$log    = Join-Path $v9   'v9_build\.v9_final_export.log'

if (-not (Test-Path $docx)) { throw "DOCX not found: $docx" }
$docxHash = (Get-FileHash $docx -Algorithm SHA256).Hash

"BEGIN $(Get-Date -Format o)" | Set-Content -LiteralPath $log
"docx=$docx sha256=$docxHash" | Add-Content -LiteralPath $log

Get-ChildItem (Split-Path $work) -Filter '~$*' -Force -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath $docx -Destination $work -Force

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.AutomationSecurity = 3

try {
    # READ-ONLY open.  The document carries a static table of contents built by
    # v9_finalize_report.py, so no field/TOC evaluation is needed or wanted.
    #
    # Measured on this host: TablesOfContents.Update(), Documents.Fields.Update()
    # and ComputeStatistics() each failed to return (Word span indefinitely with
    # no dialog).  Opening read-only and SaveAs2 alone completes in ~5 s, which
    # is the path used here.  Nothing may be added to the open/export block
    # without re-timing it.
    $doc = $word.Documents.Open($work, $false, $true, $false)
    "opened_readonly" | Add-Content -LiteralPath $log
    try {
        if (Test-Path $pdf) { Remove-Item -LiteralPath $pdf -Force }
        $doc.SaveAs2($pdf, 17)
        "saved=$pdf" | Add-Content -LiteralPath $log
    } finally {
        $doc.Close(0)
    }
} finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [GC]::Collect()
    Remove-Item -LiteralPath $work -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $pdf)) { throw "PDF export produced no file: $pdf" }
$pdfBytes = (Get-Item -LiteralPath $pdf).Length
if ($pdfBytes -le 0) { throw "PDF is empty: $pdf" }

# retain an organised copy in V9/ and confirm the DOCX was not modified
Copy-Item -LiteralPath $pdf -Destination $pdfV9 -Force
$docxHashAfter = (Get-FileHash $docx -Algorithm SHA256).Hash
if ($docxHashAfter -ne $docxHash) { throw "source DOCX changed during export" }

"BYTES=$pdfBytes" | Add-Content -LiteralPath $log
"DOCX_UNCHANGED=$($docxHashAfter -eq $docxHash)" | Add-Content -LiteralPath $log
"DONE" | Add-Content -LiteralPath $log

Write-Host "PDF=$pdf"
Write-Host "BYTES=$pdfBytes"
Write-Host "DOCX_SHA256_UNCHANGED=True"
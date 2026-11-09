# ReMedFiLM V8 - DOCX to PDF via native Word export.
# Word COM is used so the PDF is the exact layout of the DOCX (not a second renderer).
# The DOCX is copied to a neutral working name before opening: Word caches crashed
# document-recovery state by the original long filename and refuses to reopen it.
# All paths are ASCII. Analysis-only: no training or inference is performed.
$ErrorActionPreference = 'Stop'

$root = 'D:\Softfors\jup'
$fdr  = Join-Path $root 'full_doc_report'
$docx = Join-Path $fdr 'ReMedFiLM_Complete_Scientific_Report_V8.docx'
$pdf  = Join-Path $fdr 'ReMedFiLM_Complete_Scientific_Report_V8.pdf'
$work = Join-Path $fdr 'v8_build\.v8_word_work.docx'

if (-not (Test-Path $docx)) { throw "DOCX not found: $docx" }

# Clear any stale Word lock/recovery for the working file.
Get-ChildItem (Split-Path $work) -Filter '~$*' -Force -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
Copy-Item $docx $work -Force

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.AutomationSecurity = 3

try {
    $doc = $word.Documents.Open($work, $false, $false, $false)
    try {
        # Update fields in every story (body, header, footer) so PAGE / NUMPAGES resolve.
        foreach ($story in $doc.StoryRanges) {
            $story.Fields.Update() | Out-Null
            $next = $story.NextStoryRange
            while ($null -ne $next) {
                $next.Fields.Update() | Out-Null
                $next = $next.NextStoryRange
            }
        }

        $doc.Repaginate()
        foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }
        $doc.Repaginate()
        foreach ($toc in $doc.TablesOfContents) { $toc.UpdatePageNumbers() | Out-Null }

        $pages = $doc.ComputeStatistics(2)   # wdStatisticPages

        # ExportAsFixedFormat is used instead of SaveAs2: Word's SaveAs2 PDF
        # path crashes on this 33-image document, while the fixed-format
        # exporter completes reliably.
        # (OutputFileName, ExportFormat=17 wdExportFormatPDF,
        #  OpenAfterExport, OptimizeFor=0 print, Range=0 all document,
        #  From, To, Item, IncludeDocProps, KeepIRM, CreateBookmarks=0 none,
        #  DocStructureTags, BitmapMissingFonts, UseISO19005_1)
        $doc.ExportAsFixedFormat($pdf, 17, $false, 0, 0, 1, 1, 0,
                                 $true, $true, 0, $true, $true, $false)
        "PAGES=$pages"
        "PDF=$pdf"
    } finally {
        $doc.Close(0)                        # wdDoNotSaveChanges
    }
} finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    Remove-Item $work -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $pdf)) { throw "PDF export produced no file" }
"BYTES=" + (Get-Item $pdf).Length

$ErrorActionPreference = 'Stop'
$root = 'D:\Softfors\jup'
$fdr  = Join-Path $root 'full_doc_report'
$work = Join-Path $fdr 'v8_build\.v8_word_work.docx'
$pdf  = Join-Path $fdr 'ReMedFiLM_Complete_Scientific_Report_V8.pdf'
$log  = Join-Path $fdr 'v8_build\.export.log'
"BEGIN $(Get-Date -Format o)" | Set-Content $log
function L($m) { "$(Get-Date -Format o)  $m" | Add-Content $log }
try {
    $w = New-Object -ComObject Word.Application
    $w.Visible = $false; $w.DisplayAlerts = 0; $w.AutomationSecurity = 3
    L 'word created'
    $d = $w.Documents.Open($work, $false, $false, $false)
    L ('opened paragraphs=' + $d.Paragraphs.Count)
    L 'update body fields'
    $d.Fields.Update() | Out-Null
    L 'update stories'
    foreach ($s in $d.StoryRanges) { $s.Fields.Update() | Out-Null }
    L 'repaginate 1'
    $d.Repaginate()
    L ('pages1=' + $d.ComputeStatistics(2))
    L 'toc count'
    L ('toc=' + $d.TablesOfContents.Count)
    foreach ($t in $d.TablesOfContents) { $t.Update() | Out-Null }
    L 'toc updated'
    $d.Repaginate()
    foreach ($t in $d.TablesOfContents) { $t.UpdatePageNumbers() | Out-Null }
    L ('pages2=' + $d.ComputeStatistics(2))
    L 'saveas'
    $d.SaveAs2($pdf, 17)
    L 'saved'
    $d.Close(0); $w.Quit()
    L 'DONE'
} catch {
    L ('ERROR: ' + $_.Exception.Message.Split("`n")[0])
    try { $d.Close(0) } catch {}
    try { $w.Quit() } catch {}
}
'END'

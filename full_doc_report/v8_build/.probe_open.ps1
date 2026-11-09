param([string]$Target)
$log = $Target + '.log'
"BEGIN $Target" | Set-Content $log
try {
    $w = New-Object -ComObject Word.Application
    $w.Visible = $false; $w.DisplayAlerts = 0; $w.AutomationSecurity = 3
    'word created' | Add-Content $log
    $d = $w.Documents.Open($Target, $false, $true, $false)
    ('opened paragraphs=' + $d.Paragraphs.Count) | Add-Content $log
    $d.Repaginate()
    ('pages=' + $d.ComputeStatistics(2)) | Add-Content $log
    $d.Close(0); $w.Quit()
    'OK' | Add-Content $log
} catch {
    ('ERROR: ' + $_.Exception.Message) | Add-Content $log
    try { $w.Quit() } catch {}
}

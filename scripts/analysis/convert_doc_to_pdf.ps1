$docx = "D:\Softfors\jup\full_doc_report\RA_MedFiLM_BARR_Visual_Research_Report_V3.docx"
$pdf = "D:\Softfors\jup\full_doc_report\RA_MedFiLM_BARR_Visual_Research_Report_V3.pdf"

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $doc = $word.Documents.Open($docx)
    $doc.SaveAs([ref]$pdf, [ref]17)
    $doc.Close()
    $word.Quit()
    Write-Host "Word COM conversion to PDF succeeded!"
} catch {
    Write-Host "Word COM error: $($_.Exception.Message)"
}

param(
    [Parameter(Mandatory = $true)][string]$InputDocx,
    [Parameter(Mandatory = $true)][string]$OutputPdf
)

$ErrorActionPreference = "Stop"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($InputDocx, $false, $true)
    $doc.ExportAsFixedFormat($OutputPdf, 17)
    $doc.Close($false)
}
finally {
    $word.Quit()
}
Write-Output $OutputPdf

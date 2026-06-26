param(
    [string]$OutputPath = "test-statement.pdf",
    [string]$AccountSuffix = "7890",
    [string]$BankName = "Your Bank"
)

# Generate a simple test PDF
$pdfContent = @"
%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj

3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj

4 0 obj
<< /Length 244 >>
stream
BT
/F1 24 Tf
100 700 Td
($BankName - Monthly Statement) Tj
/F1 14 Tf
50 650 Td
(Account: ****$AccountSuffix) Tj
50 620 Td
(Statement Period: January 2026) Tj
50 580 Td
(Transaction History:) Tj
/F1 12 Tf
70 550 Td
(2026-01-05  Deposit             \$1,500.00) Tj
70 530 Td
(2026-01-12  Withdrawal          \$250.00) Tj
70 510 Td
(2026-01-20  Deposit             \$3,200.00) Tj
70 480 Td
(2026-01-28  Withdrawal          \$175.00) Tj
/F1 14 Tf
50 430 Td
(Ending Balance: \$4,275.00) Tj
/F1 10 Tf
50 50 Td
(This is a CUSTOM replacement statement created for testing.) Tj
ET
endstream
endobj

5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000562 00000 n 

trailer
<< /Size 6 /Root 1 0 R >>
startxref
610
%%EOF
"@

Set-Content -Path $OutputPath -Value $pdfContent -Encoding Ascii
Write-Host "Test PDF generated: $OutputPath" -ForegroundColor Green
Write-Host ""
Write-Host "To upload this PDF, run:"
Write-Host "  curl -X POST http://localhost:8080/api/statements/upload -F ""accountId=1234567890"" -F ""file=@$OutputPath""" -ForegroundColor Cyan
Write-Host ""
Write-Host "Then open in browser: http://localhost:8080/api/statements/replace?accountId=1234567890" -ForegroundColor Cyan

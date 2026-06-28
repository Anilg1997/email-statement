@echo off
REM =============================================================
REM Bank Statement Replacer - Upload Test PDF
REM =============================================================
REM Usage: drag a PDF onto this batch file, or run:
REM   upload-test-pdf.bat "C:\path\to\your-statement.pdf"
REM =============================================================

set SERVER_URL=http://localhost:8080
set ACCOUNT_ID=1234567890

if "%1"=="" (
    echo.
    echo ==================================================
    echo  Bank Statement PDF Uploader
    echo ==================================================
    echo.
    echo  Usage: Drag and drop a PDF file onto this script,
    echo         or run: %0 "C:\path\to\file.pdf"
    echo.
    echo  Default Account ID: %ACCOUNT_ID%
    echo  Server URL: %SERVER_URL%
    echo.
    echo ==================================================
    echo.
    set /p ACCOUNT_ID="Enter Account ID (or press Enter for default): "
    set /p PDF_PATH="Enter path to PDF file: "
) else (
    set PDF_PATH=%1
)

echo.
echo Uploading %PDF_PATH% for account %ACCOUNT_ID%...
curl -X POST "%SERVER_URL%/api/statements/upload" ^
  -F "accountId=%ACCOUNT_ID%" ^
  -F "file=@%PDF_PATH%"

echo.
echo.
echo Done! Press any key to exit...
pause > nul

Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -like '*chatgpt-data*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 3
Remove-Item -LiteralPath (Join-Path $env:CHATGPT_BRIDGE 'chatgpt-data\SingletonLock') -Force -ErrorAction SilentlyContinue

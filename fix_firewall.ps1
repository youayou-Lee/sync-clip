# PowerShell script to add firewall rule for UDP broadcast
# Run as Administrator

Write-Host "Adding firewall rule for UDP clipboard sync..." -ForegroundColor Green

# Remove existing rule if it exists
Remove-NetFirewallRule -DisplayName "SyncClip UDP" -ErrorAction SilentlyContinue

# Add new rule allowing UDP inbound on ports 5555-5559
New-NetFirewallRule -DisplayName "SyncClip UDP" -Direction Inbound -Protocol UDP -LocalPort 5555-5559 -Action Allow -Profile Any

Write-Host "Firewall rule added successfully!" -ForegroundColor Green
Write-Host "You can now test the clipboard synchronization." -ForegroundColor Yellow
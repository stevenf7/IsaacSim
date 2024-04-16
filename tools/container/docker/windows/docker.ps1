param (
    [switch]$reboot=$false
)

$hyperv = Get-WindowsOptionalFeature -FeatureName Microsoft-Hyper-V-All -Online
if($hyperv.State -eq "Enabled") {
    Write-Host "Hyper-V is enabled. Skipping install."
} else {
    Write-Host "Installing Hyper-V."
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All -NoRestart
}

Write-Host "Installing Docker Desktop For Windows."
& "$PSScriptRoot\Docker for Windows Installer.exe" install --quiet | out-null
Copy-Item "$PSScriptRoot\settings.json" $env:APPDATA\Docker\settings.json
Write-Host "Finished."

if($reboot) {
    Write-Host "Rebooting."
    shutdown.exe -r -f -t 0
} else {
    Write-Host "Please reboot to finish Docker install."
    pause
}



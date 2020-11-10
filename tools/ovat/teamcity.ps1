$ErrorActionPreference = "Stop"
# Where are the tools located in relation to this script
$TOOLS = $PSScriptRoot + "\.."
$PACKMAN = "$TOOLS\packman"
# Initialize TeamCity Python
$CWD = (Get-Location).Path
Write-Host "Current directory: ${CWD}"

Write-Host "Creating virtual environment and installing ovat-client"
& $PACKMAN\python.bat -m venv _venv
.\_venv\Scripts\activate.ps1
python -m pip install -U pip
pip config set --site global.extra-index-url https://pypi.perflab.nvidia.com/simple
pip install -U ovat-client>=0.17.0

Write-Host "Running tests"
ovat jobs create-from-file -e teamcity
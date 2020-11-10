$TOOLS = $PSScriptRoot + "\tools"

# Initialize TeamCity Python
Write-Host "Current directory: ${(Get-Location).Path}"

Write-Host "Creating virtual environment and installing ovat-client"
py -3.7 -m venv _venv
.\_venv\Scripts\activate.ps1
python -m pip install -U pip
pip config set --site global.extra-index-url https://pypi.perflab.nvidia.com/simple
pip install -U ovat-client==0.17.0-rc.4

Write-Host "Running tests"
ovat jobs create-from-file -e teamcity
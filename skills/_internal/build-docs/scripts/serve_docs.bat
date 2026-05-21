@echo off
REM SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
REM SPDX-License-Identifier: Apache-2.0

setlocal

set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%\..\..\..\.."
set "DOCS_DIR=%REPO_ROOT%\_build\docs\isaac-sim\latest"
set "PORT=%~1"
if "%PORT%"=="" set "PORT=8000"

if not exist "%DOCS_DIR%" (
    echo ERROR: Docs build output not found at %DOCS_DIR%
    echo Run the docs build first:  tools\build_docs.bat
    exit /b 1
)

echo Serving docs from: %DOCS_DIR%
echo   User Guide: http://localhost:%PORT%
echo   API Docs:   http://localhost:%PORT%/py/
echo.
echo Press Ctrl+C to stop.

cd /d "%DOCS_DIR%"
python -m http.server %PORT%

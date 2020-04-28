@echo off

:: Verify formatting
echo ##teamcity[progressMessage 'Verify formatting...']
call "%~dp0..\..\..\..\format_code.bat" --verify
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Full rebuild
echo ##teamcity[progressMessage 'Full rebuild...']
call "%~dp0..\..\..\..\build.bat" -x
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Docs
echo ##teamcity[progressMessage 'Docs...']
call "%~dp0..\..\..\build_docs.bat" -c release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Gather licenses
echo ##teamcity[progressMessage 'Gather licenses...']
call "%~dp0..\..\..\licensing.bat" ^
gather ^
-p %~dp0..\..\..\..\deps\isaac-sim.packman.xml ^
%~dp0..\..\..\..\deps\kit-sdk.packman.xml ^
%~dp0..\..\..\..\deps\rtx-plugins.packman.xml ^
%~dp0..\..\..\..\deps\omni-physics.packman.xml ^
-d %~dp0..\..\..\..\_build
if %errorlevel% neq 0 ( exit /b %errorlevel% )

REM :: Validate licenses
REM echo ##teamcity[progressMessage 'Validate licenses...']
REM if not "%1" == "--debug-only" (
REM     call "%~dp0..\..\..\licensing.bat" ^
REM     validate ^
REM     -p %~dp0..\..\..\..\deps\isaac-sim.packman.xml ^
REM     %~dp0..\..\..\..\deps\kit-sdk.packman.xml ^
REM     %~dp0..\..\..\..\deps\rtx-plugins.packman.xml ^
REM     %~dp0..\..\..\..\deps\omni-physics.packman.xml ^
REM     -d %~dp0..\..\..\..\_build ^
REM     -b windows-x86_64\release
REM )

:: Run python tests
::echo ##teamcity[progressMessage 'Python tests...']
::call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config release
::if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Run kit tests 
::echo ##teamcity[progressMessage 'Kit tests...']
:: SKIP THEM for now, that puts a hard requirement on TC agent (to have RTX, driver version, etc.)
::call "%~dp0..\..\test_runner.bat" --suite kittests --config release
::if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Package
echo ##teamcity[progressMessage 'Packaging...']
call "%~dp0..\..\..\package.bat" -m test_runner
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\..\..\package.bat" -m docs
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\..\..\package.bat" -m omni_isaac_sim -c debug
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\..\..\package.bat" -m omni_isaac_sim -c release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\..\..\package.bat" -m omni_domain_randomization -c debug
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\..\..\package.bat" -m omni_domain_randomization -c release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: publish artifacts to teamcity
echo ##teamcity[publishArtifacts '_build/packages']



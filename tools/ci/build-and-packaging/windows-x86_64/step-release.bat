@echo off

if not defined TEAMCITY_VERSION (
    :: Verify formatting
    echo ##teamcity[blockOpened name='Verify formatting...']
    call "%~dp0..\..\..\..\format_code.bat" --verify
    echo ##teamcity[blockClosed name='Verify formatting...']
)
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Full rebuild
echo ##teamcity[blockOpened name='Full rebuild...']
call "%~dp0..\..\..\..\build.bat" -c
call "%~dp0..\..\..\..\build.bat" -r
if %errorlevel% neq 0 ( exit /b %errorlevel% )
echo ##teamcity[blockClosed name='Full rebuild...']

:: Docs
REM echo ##teamcity[blockOpened name='Docs...']
REM call "%~dp0..\..\..\build_docs.bat" -c release
REM if %errorlevel% neq 0 ( exit /b %errorlevel% )
REM echo ##teamcity[blockClosed name='Docs...']

:: Gather licenses
echo ##teamcity[blockOpened name='Gather licenses...']
call "%~dp0..\..\..\licensing.bat" ^
gather ^
-p %~dp0..\..\..\..\deps\isaac-sim.packman.xml ^
%~dp0..\..\..\..\deps\kit-sdk.packman.xml ^
%~dp0..\..\..\..\deps\rtx-plugins.packman.xml ^
%~dp0..\..\..\..\deps\omni-physics.packman.xml ^
-d %~dp0..\..\..\..
if %errorlevel% neq 0 ( exit /b %errorlevel% )
echo ##teamcity[blockClosed name='Gather licenses...']

REM :: Validate licenses
REM echo ##teamcity[blockOpened name='Validate licenses...']
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
REM echo ##teamcity[blockClosed name='Validate licenses...']

:: Package
echo ##teamcity[blockOpened name='Build packages...']
echo ##teamcity[progressMessage 'Packaging test_runner...']
call "%~dp0..\..\..\package.bat" -m test_runner -c release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

echo ##teamcity[progressMessage 'Packaging docs...']
call "%~dp0..\..\..\package.bat" -m docs -c release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

echo ##teamcity[progressMessage 'Packaging isaac-sim...']
call "%~dp0..\..\..\package.bat" -m isaac-sim -c release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

echo ##teamcity[progressMessage 'Packaging omniverse-kit-robotics...']
call "%~dp0..\..\..\package.bat" -m omniverse-kit-robotics -c release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

echo ##teamcity[progressMessage 'Packaging omni_domain_randomization...']
call "%~dp0..\..\..\package.bat" -m omni_domain_randomization -c release
if %errorlevel% neq 0 ( exit /b %errorlevel% )
echo ##teamcity[blockClosed name='Build packages...']

:: publish artifacts to teamcity
echo ##teamcity[publishArtifacts '_build/packages']

@echo off

pushd "%~dp0..\..\..\.."

if not defined TEAMCITY_VERSION (
    :: Verify formatting
    echo ##teamcity[blockOpened name='Verify formatting...']
    call "format_code.bat" --verify
    echo ##teamcity[blockClosed name='Verify formatting...']
)
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Full rebuild
echo ##teamcity[blockOpened name='Full rebuild...']
call "build.bat" -c
call "build.bat" -r
if %errorlevel% neq 0 ( exit /b %errorlevel% )
echo ##teamcity[blockClosed name='Full rebuild...']

:: Docs
REM echo ##teamcity[blockOpened name='Docs...']
REM call "%~dp0..\..\..\build_docs.bat" -c release
REM if %errorlevel% neq 0 ( exit /b %errorlevel% )
REM echo ##teamcity[blockClosed name='Docs...']

:: Gather licenses
echo ##teamcity[blockOpened name='Gather licenses...']
call "tools\gather_licenses.bat"
if %errorlevel% neq 0 (
    echo ##teamcity[buildStatus text='Licensing validation failed.' status='FAILURE']
    exit /b %errorlevel%
)
echo ##teamcity[blockClosed name='Gather licenses...']

:: Validate licenses
echo ##teamcity[blockOpened name='Validate licenses...']
if not "%1" == "--debug-only" (
    call "tools\licensing.bat" validate %TAGPACKAGES% ^
    -d %cd% ^
    -p deps\isaac-sim.packman.xml ^
    -b _build\windows-x86_64\release\
)
if %errorlevel% neq 0 ( goto Error )
echo ##teamcity[blockClosed name='Validate licenses...']

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

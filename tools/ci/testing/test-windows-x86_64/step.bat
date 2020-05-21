@echo off
setlocal

if defined TEAMCITY_VERSION (
    set "package=--from-package"
)

:: Python Tests - DX12
echo ##teamcity[testSuiteStarted name='isaac-sim-pythontests-dx12']
call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config release %package%
REM if %errorlevel% neq 0 (
REM     echo ##teamcity[buildStatus text='Failed running isaac-sim-pythontests-dx12 Python tests' status='FAILURE']
REM     exit /b %errorlevel%
REM )
echo ##teamcity[testSuiteFinished name='isaac-sim-pythontests-dx12']

:: Python Tests - Vulkan
echo ##teamcity[testSuiteStarted name='isaac-sim-pythontests-vulkan']
call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config release %package% -e="--vulkan"
REM if %errorlevel% neq 0 (
REM     echo ##teamcity[buildStatus text='Failed running isaac-sim-pythontests-vulkan Python tests' status='FAILURE']
REM     exit /b %errorlevel%
REM )
echo ##teamcity[testSuiteFinished name='isaac-sim-pythontests-vulkan']

if not defined TEAMCITY_VERSION (
    goto :Success
)

set "ARCHIVE_PATTERN=_builtpackages\omniverse-kit-robotics*.7z"

:: Python Tests - DX12
echo ##teamcity[testSuiteStarted name='omniverse-kit-pythontests-robotics-dx12']
call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config release %package%
REM if %errorlevel% neq 0 (
REM     echo ##teamcity[buildStatus text='Failed running omniverse-kit-robotics-pythontests-dx12 Python tests' status='FAILURE']
REM     exit /b %errorlevel%
REM )
echo ##teamcity[testSuiteFinished name='omniverse-kit-pythontests-robotics-dx12']

:: Python Tests - Vulkan
echo ##teamcity[testSuiteStarted name='omniverse-kit-pythontests-robotics-vulkan']
call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config release %package% -e="--vulkan"
REM if %errorlevel% neq 0 (
REM     echo ##teamcity[buildStatus text='Failed running omniverse-kit-robotics-pythontests-vulkan Python tests' status='FAILURE']
REM     exit /b %errorlevel%
REM )
echo ##teamcity[testSuiteFinished name='omniverse-kit-robotics-pythontests-vulkan']

:Success
exit /b 0
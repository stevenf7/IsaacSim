@echo off
setlocal

if defined TEAMCITY_VERSION (
    set "package=--from-package"
)

:: Python Tests - DX12
echo ##teamcity[testSuiteStarted name='isaac-sim-pythontests-dx12-release']
call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config release %package%
echo ##teamcity[testSuiteFinished name='isaac-sim-pythontests-dx12-release']

:: Python Tests - Vulkan
echo ##teamcity[testSuiteStarted name='isaac-sim-pythontests-vulkan-release']
call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config release %package% -e="--vulkan"
echo ##teamcity[testSuiteFinished name='isaac-sim-pythontests-vulkan-release']

REM if not defined TEAMCITY_VERSION (
REM     goto :Success
REM )

REM set "ARCHIVE_PATTERN=_builtpackages\omniverse-kit-robotics*.7z"

REM :: Python Tests - DX12
REM echo ##teamcity[testSuiteStarted name='omniverse-kit-robotics-pythontests-dx12-release']
REM call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config release %package%
REM echo ##teamcity[testSuiteFinished name='omniverse-kit-robotics-pythontests-dx12-release']

REM :: Python Tests - Vulkan
REM echo ##teamcity[testSuiteStarted name='omniverse-kit-robotics-pythontests-vulkan-release']
REM call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config release %package% -e="--vulkan"
REM echo ##teamcity[testSuiteFinished name='omniverse-kit-robotics-pythontests-vulkan-release']

:Success
exit /b 0
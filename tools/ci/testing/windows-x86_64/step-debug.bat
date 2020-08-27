@echo off
setlocal

if defined TEAMCITY_VERSION (
    set "package=--from-package"
)

:: Python Tests - DX12
echo ##teamcity[testSuiteStarted name='isaac-sim-pythontests-dx12-debug']
call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config debug %package%
echo ##teamcity[testSuiteFinished name='isaac-sim-pythontests-dx12-debug']

:: Python Tests - Vulkan
echo ##teamcity[testSuiteStarted name='isaac-sim-pythontests-vulkan-debug']
call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config debug %package% -e="--vulkan"
echo ##teamcity[testSuiteFinished name='isaac-sim-pythontests-vulkan-debug']

REM if not defined TEAMCITY_VERSION (
REM     goto :Success
REM )

REM set "ARCHIVE_PATTERN=_builtpackages\omniverse-kit-robotics*.7z"

REM :: Python Tests - DX12
REM echo ##teamcity[testSuiteStarted name='omniverse-kit-robotics-pythontests-dx12-debug']
REM call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config debug %package%
REM echo ##teamcity[testSuiteFinished name='omniverse-kit-robotics-pythontests-dx12-debug']

REM :: Python Tests - Vulkan
REM echo ##teamcity[testSuiteStarted name='omniverse-kit-robotics-pythontests-vulkan-debug']
REM call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config debug %package% -e="--vulkan"
REM echo ##teamcity[testSuiteFinished name='omniverse-kit-robotics-pythontests-vulkan-debug']

:Success
exit /b 0
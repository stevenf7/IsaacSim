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

if not defined TEAMCITY_VERSION (
    goto :Success
)

set "ARCHIVE_PATTERN=_builtpackages\omniverse-kit-robotics*.7z"

:: Python Tests - DX12
echo ##teamcity[testSuiteStarted name='omniverse-kit-robotics-pythontests-dx12-debug']
call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config debug %package%
echo ##teamcity[testSuiteFinished name='omniverse-kit-robotics-pythontests-dx12-debug']

:: Python Tests - Vulkan
echo ##teamcity[testSuiteStarted name='omniverse-kit-robotics-pythontests-vulkan-debug']
call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config debug %package% -e="--vulkan"
echo ##teamcity[testSuiteFinished name='omniverse-kit-robotics-pythontests-vulkan-debug']

:Success
exit /b 0
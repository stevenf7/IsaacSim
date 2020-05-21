@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

if defined TEAMCITY_VERSION (
    set "package=--from-package"
)

:: DX12 Startup Test
echo ##teamcity[testSuiteStarted name='isaac-sim-startuptests-dx12']
call "%SCRIPT_DIR%..\..\..\test_runner.bat" --suite startuptest --config release %package% --clean -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" %*
REM if %errorlevel% neq 0 (
REM     echo ##teamcity[buildStatus text='Failed running isaac-sim-startuptests-dx12 test' status='FAILURE']
REM     exit /b %errorlevel%
REM )
echo ##teamcity[testSuiteFinished name='isaac-sim-startuptests-dx12']

:: Vulkan Startup Test
echo ##teamcity[testSuiteStarted name='isaac-sim-startuptests-vulkan']
call "%SCRIPT_DIR%..\..\..\test_runner.bat" --suite startuptest --config release %package% -e="--vulkan" -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" %*
REM if %errorlevel% neq 0 (
REM     echo ##teamcity[buildStatus text='Failed running isaac-sim-startuptests-vulkan test' status='FAILURE']
REM     exit /b %errorlevel%
REM )
echo ##teamcity[testSuiteFinished name='isaac-sim-startuptests-vulkan']

if not defined TEAMCITY_VERSION (
    goto :Success
)

:: Packaging the shader cache
echo ##teamcity[blockOpened name='Packaging the shader cache...']
call "%SCRIPT_DIR%..\..\..\packman\python.bat" "%SCRIPT_DIR%..\..\..\repoman\package_cache.py" --platform windows-x86_64 --config release --experience isaac-sim %*
REM if %errorlevel% neq 0 (
REM     echo ##teamcity[buildStatus text='Failed packaging the shader cache' status='FAILURE']
REM     exit /b %errorlevel%
REM )
echo ##teamcity[blockClosed name='Packaging the shader cache...']

:: publish artifacts to teamcity
echo ##teamcity[publishArtifacts '_builtpackages/isaac-sim*']




set "ARCHIVE_PATTERN=_builtpackages\omniverse-kit-robotics*.7z"

:: DX12 Startup Test
echo ##teamcity[testSuiteStarted name='omniverse-kit-robotics-startuptests-dx12']
call "%SCRIPT_DIR%..\..\..\test_runner.bat" --suite startuptest --config release %package% --clean -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" %*
REM if %errorlevel% neq 0 (
REM     echo ##teamcity[buildStatus text='Failed running omniverse-kit-robotics-startuptests-dx12 test' status='FAILURE']
REM     exit /b %errorlevel%
REM )
echo ##teamcity[testSuiteFinished name='omniverse-kit-robotics-startuptests-dx12']

:: Vulkan Startup Test
echo ##teamcity[testSuiteStarted name='omniverse-kit-robotics-startuptests-vulkan']
call "%SCRIPT_DIR%..\..\..\test_runner.bat" --suite startuptest --config release %package% -e="--vulkan" -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" %*
REM if %errorlevel% neq 0 (
REM     echo ##teamcity[buildStatus text='Failed running omniverse-kit-robotics-startuptests-vulkan test' status='FAILURE']
REM     exit /b %errorlevel%
REM )
echo ##teamcity[testSuiteFinished name='omniverse-kit-robotics-startuptests-vulkan']

:: Packaging the shader cache
echo ##teamcity[blockOpened name='Packaging the shader cache...']
if "%package%" == "--from-package" (
    call "%SCRIPT_DIR%..\..\..\packman\python.bat" "%SCRIPT_DIR%..\..\..\repoman\package_cache.py" --platform windows-x86_64 --config release --experience omniverse-kit-robotics %*
)
REM if %errorlevel% neq 0 (
REM     echo ##teamcity[buildStatus text='Failed packaging the shader cache' status='FAILURE']
REM     exit /b %errorlevel%
REM )
echo ##teamcity[blockClosed name='Packaging the shader cache...']

:: publish artifacts to teamcity
echo ##teamcity[publishArtifacts '_builtpackages/omniverse-kit-robotics*']

:Success
exit /b 0
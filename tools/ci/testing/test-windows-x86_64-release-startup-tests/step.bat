@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

if defined TEAMCITY_VERSION (
    set "package=--from-package"
)

REM :: DX12 Startup Test
REM call "%SCRIPT_DIR%..\..\..\test_runner.bat" --suite startuptest --config release %package% -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" %*
REM if %errorlevel% neq 0 (
REM     echo ##teamcity[buildStatus text='Failed running DX12 startup test' status='FAILURE']
REM     exit /b %errorlevel%
REM )

REM :: Vulkan Startup Test
REM call "%SCRIPT_DIR%..\..\..\test_runner.bat" --suite startuptest --config release %package% -e="--vulkan" -e="--carb/rtx/shaderDb/obfuscateCode=true" -e="--carb/rtx/materialDb/compileMdlAsLibrary=true" %*
REM if %errorlevel% neq 0 (
REM     echo ##teamcity[buildStatus text='Failed running Vulkan startup test' status='FAILURE']
REM     exit /b %errorlevel%
REM )

REM :: packaging the shader cache
REM if "%package%" == "--from-package" (
REM     call "%SCRIPT_DIR%..\..\..\packman\python.bat" "%SCRIPT_DIR%..\..\..\repoman\package_cache.py" --platform windows-x86_64 --config release %*
REM )
REM if %errorlevel% neq 0 (
REM     echo ##teamcity[buildStatus text='Failed packaging the shader cache' status='FAILURE']
REM     exit /b %errorlevel%
REM )

:: publish artifacts to teamcity
echo ##teamcity[publishArtifacts '_builtpackages/*']

:Success
exit /b 0
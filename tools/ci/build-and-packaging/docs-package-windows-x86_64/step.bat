@echo off

:: build release
call "%~dp0..\..\..\..\build.bat" --release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: build docs
call "%~dp0..\..\..\..\repo.bat" omnigraph_docs
@REM if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: build docs
call "%~dp0..\..\..\..\repo.bat" docs --config release --warn-as-error=0
@REM if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: create launcher package
@REM call "%~dp0..\..\..\..\repo.bat" package -m isaac-sim-standalone -c release
@REM if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: create internal package
@REM call "%~dp0..\..\..\..\repo.bat" package -m isaac-sim-internal -c release
@REM if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Package test runner for TC
@REM call "%~dp0..\..\..\..\repo.bat" package -m test_runner
@REM if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Packaging docs
call "%~dp0..\..\..\..\repo.bat" package -m docs
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: publish artifacts to teamcity
echo ##teamcity[publishArtifacts '_build/packages']



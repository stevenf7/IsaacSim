@echo off

:: Package launcher images
call "%~dp0package.bat" --mode isaac-sim-pipeline-images-beta
if %errorlevel% neq 0 ( exit /b %errorlevel% )
call "%~dp0package.bat" --mode isaac-sim-pipeline-images-rc
if %errorlevel% neq 0 ( exit /b %errorlevel% )
call "%~dp0package.bat" --mode isaac-sim-pipeline-images-assets
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\repo.bat" publish_launcher_images
if %errorlevel% neq 0 ( exit /b %errorlevel% )

@echo off

:: Veify formatting
::call "%~dp0..\..\..\..\format_code.bat" --verify
::if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Full rebuild
call "%~dp0..\..\..\..\build.bat" -x -d
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\..\..\..\build.bat" -x -r
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Docs
::call "%~dp0..\..\build_docs.bat" -c release
::if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Run python tests
:: call "%~dp0..\..\..\test.bat" --suite pythontests --config release
:: if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Run startup tests
:: call "%~dp0..\..\..\test.bat" --suite startuptests --config release
:: if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Package
call "%~dp0..\..\..\..\repo.bat" package -c release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: publish artifacts to teamcity
echo ##teamcity[publishArtifacts '_build/packages']



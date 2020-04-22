@echo off

:: Verify formatting
echo ##teamcity[progressMessage 'Verify formatting...']
call "%~dp0..\..\..\..\format_code.bat" --verify
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Full rebuild
echo ##teamcity[progressMessage 'Full rebuild...']
call "%~dp0..\..\..\..\build.bat" -x
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Docs
echo ##teamcity[progressMessage 'Docs...']
call "%~dp0..\..\..\build_docs.bat" -c release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Run python tests
::echo ##teamcity[progressMessage 'Python tests...']
::call "%~dp0..\..\..\test_runner.bat" --suite pythontests --config release
::if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Run kit tests 
::echo ##teamcity[progressMessage 'Kit tests...']
:: SKIP THEM for now, that puts a hard requirement on TC agent (to have RTX, driver version, etc.)
::call "%~dp0..\..\test_runner.bat" --suite kittests --config release
::if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: Package
echo ##teamcity[progressMessage 'Packaging...']
call "%~dp0..\..\..\package.bat" -m test_runner
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\..\..\package.bat" -m docs
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\..\..\package.bat" -m omniverse-kit -c release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\..\..\package.bat" -m omni_isaac_sim -c debug
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\..\..\package.bat" -m omni_isaac_sim -c release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\..\..\package.bat" -m omni_domain_randomization -c debug
if %errorlevel% neq 0 ( exit /b %errorlevel% )

call "%~dp0..\..\..\package.bat" -m omni_domain_randomization -c release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: publish artifacts to teamcity
echo ##teamcity[publishArtifacts '_build/packages']



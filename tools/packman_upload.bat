@echo off

::set PM_S3_ID=
::set PM_S3_KEY=

%~dp0packman\packman.cmd push -r cloudfront_upload -v -mp %*
if %errorlevel% neq 0 ( exit /b %errorlevel% )

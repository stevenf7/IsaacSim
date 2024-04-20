@echo off
setlocal

echo "Clearing Caches Script"
echo "Note: This script will delete folders on you system and is not reversible."

:SHADERCACHE
SET "CLEAR_PATH=%userprofile%\AppData\Local\ov\cache\shaders"
echo.
echo Clearing shader cache... (%CLEAR_PATH%)
SET /P AREYOUSURE=Are you sure (Y/[N])?
IF /I "%AREYOUSURE%" NEQ "Y" GOTO TEXTURECACHE
del /S /F /Q %CLEAR_PATH%
echo Clearing shader cache DONE.

:TEXTURECACHE
SET "CLEAR_PATH=%userprofile%\AppData\Local\ov\cache\texturecache"
echo.
echo Clearing texturecache... (%CLEAR_PATH%)
SET /P AREYOUSURE=Are you sure (Y/[N])?
IF /I "%AREYOUSURE%" NEQ "Y" GOTO KITCACHE
del /S /F /Q %CLEAR_PATH%
echo Clearing texturecache DONE.

:KITCACHE
SET "CLEAR_PATH=%userprofile%\AppData\Local\ov\cache\Kit\106.0"
echo.
echo Clearing Kit cache... (%CLEAR_PATH%)
SET /P AREYOUSURE=Are you sure (Y/[N])?
IF /I "%AREYOUSURE%" NEQ "Y" GOTO END
del /S /F /Q %CLEAR_PATH%
echo Clearing Kit cache DONE.


:END
endlocal

:: Always succeed in case kit crashed or hanged
pause
exit

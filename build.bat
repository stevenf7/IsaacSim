@echo off
@REM Generate USD Schemas
call "%~dp0schemas/repo" usdgenschema
call "%~dp0schemas/repo" build
@REM Build Isaac Sim
call "%~dp0repo" build %*

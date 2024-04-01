@echo off
call "%~dp0..\repo.bat" omnigraph_docs %*
call "%~dp0..\repo.bat" docs --config release %*

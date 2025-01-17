@echo off
call "%~dp0..\repo.bat" extension_docs --error-as-warn %*
call "%~dp0..\repo.bat" docs --config release --warn-as-error=0 %*

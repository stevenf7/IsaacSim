@echo off
call "%~dp0packman\packman" pull "%~dp0..\deps\kit-sdk.packman.xml" -i release -p windows-x86_64
call "%~dp0..\repo.bat" package -m create-launcher %*

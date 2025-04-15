@echo off
setlocal

:: Add symlink to Isaac Examples
pushd "%~dp0"
if exist extension_examples cmd /c rmdir extension_examples
call mklink /D extension_examples exts\isaacsim.examples.interactive\isaacsim\examples\interactive
:: Powershell New-Item -ItemType Junction -Path "extension_examples" -Target "exts\isaacsim.examples.interactive\isaacsim\examples\interactive"
if %ERRORLEVEL% neq 0 (echo "Symlink extension_examples not created.") else (echo "Symlink extension_examples created.")
popd

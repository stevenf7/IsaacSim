@echo off
setlocal

@REM Add symlink to Isaac Examples
echo "Creating extension_examples symlink..."
if exist extension_examples cmd /c rmdir extension_examples
call mklink /D extension_examples exts\omni.isaac.examples\omni\isaac\examples
if %ERRORLEVEL% neq 0 (echo "Symlink extension_examples not created.") else (echo "Symlink extension_examples created.")

@REM Warm up shader cache
echo "Warming up cache..."
call "%~dp0omni.isaac.sim.warmup.bat"

@REM Install default Python packages 
echo "Installing Python packages..."
call "%~dp0python.sh -m pip install -r %~dp0requirements.txt

echo "Isaac Sim post installation script completed!"
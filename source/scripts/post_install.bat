REM SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
REM SPDX-License-Identifier: Apache-2.0
REM
REM Licensed under the Apache License, Version 2.0 (the "License");
REM you may not use this file except in compliance with the License.
REM You may obtain a copy of the License at
REM
REM http://www.apache.org/licenses/LICENSE-2.0
REM
REM Unless required by applicable law or agreed to in writing, software
REM distributed under the License is distributed on an "AS IS" BASIS,
REM WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
REM See the License for the specific language governing permissions and
REM limitations under the License.

@echo off
setlocal

:: Add symlink to Isaac Examples
pushd "%~dp0"
if exist extension_examples cmd /c rmdir extension_examples
call mklink /D extension_examples exts\isaacsim.examples.interactive\isaacsim\examples\interactive
:: Powershell New-Item -ItemType Junction -Path "extension_examples" -Target "exts\isaacsim.examples.interactive\isaacsim\examples\interactive"
if %ERRORLEVEL% neq 0 (echo "Symlink extension_examples not created.") else (echo "Symlink extension_examples created.")
popd

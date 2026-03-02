# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Terminal output helpers shared across Isaac Sim tooling scripts."""

from __future__ import annotations

import sys


class Colors:
    """ANSI color codes."""

    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def colorize(text: str, color: str) -> str:
    """Wrap *text* in ANSI color when stdout is a TTY."""
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.RESET}"
    return text


def header(title: str) -> None:
    """Print a section header banner."""
    print(f"\n{'=' * 72}", flush=True)
    print(colorize(f"  {title}", Colors.BOLD + Colors.CYAN), flush=True)
    print(f"{'=' * 72}", flush=True)


def log_pass(msg: str) -> None:
    print(f"  {colorize('PASS', Colors.GREEN)}  {msg}", flush=True)


def log_fail(msg: str) -> None:
    print(f"  {colorize('FAIL', Colors.RED)}  {msg}", flush=True)


def log_warn(msg: str) -> None:
    print(f"  {colorize('WARN', Colors.YELLOW)}  {msg}", flush=True)


def log_info(msg: str) -> None:
    print(f"  {colorize('INFO', Colors.DIM)}  {msg}", flush=True)

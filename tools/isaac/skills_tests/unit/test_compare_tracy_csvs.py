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

"""Unit tier: compare_tracy_csvs.py (pure stdlib CSV diff)."""

from __future__ import annotations

import pytest
from _util import load_module_from_path, skill_path

pytestmark = pytest.mark.unit

CSV_PY = skill_path("profile-isaac-sim", "scripts", "compare_tracy_csvs.py")
HEADER = "name\ttotal_ns\tcounts\tmean_ns\tmin_ns\tmax_ns"


@pytest.fixture(scope="module")
def mod():
    return load_module_from_path(CSV_PY)


def _write(path, rows, sep="\t"):
    lines = [HEADER if sep == "\t" else HEADER.replace("\t", sep)]
    for r in rows:
        lines.append(sep.join(str(x) for x in r))
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def test_load_csv_basic(mod, tmp_path):
    p = _write(tmp_path / "a.tsv", [("ZoneA", 1000, 10, 100.0, 5, 200)])
    zones = mod.load_csv(p)
    assert set(zones) == {"ZoneA"}
    assert zones["ZoneA"] == {"total_ns": 1000, "counts": 10, "mean_ns": 100.0, "min_ns": 5, "max_ns": 200}


def test_load_csv_skips_bad_rows(mod, tmp_path):
    p = tmp_path / "bad.tsv"
    p.write_text(HEADER + "\nGood\t10\t1\t10.0\t1\t10\nBad\tNaNoops\t1\t1\t1\t1\n")
    zones = mod.load_csv(str(p))
    assert "Good" in zones and "Bad" not in zones


def test_load_csv_custom_sep(mod, tmp_path):
    p = _write(tmp_path / "a.csv", [("ZoneA", 1, 1, 1.0, 1, 1)], sep=",")
    assert "ZoneA" in mod.load_csv(p, sep=",")


def test_fmt_delta(mod):
    assert mod.fmt_delta(100, 150) == "+50.0%"
    assert mod.fmt_delta(100, 50) == "-50.0%"
    assert mod.fmt_delta(0, 5) == "N/A"


def test_print_comparison_orders_and_sections(mod, capsys):
    ref = {
        "Big": {"total_ns": 9000, "counts": 9, "mean_ns": 1000.0, "min_ns": 1, "max_ns": 2},
        "Small": {"total_ns": 100, "counts": 1, "mean_ns": 100.0, "min_ns": 1, "max_ns": 2},
        "Gone": {"total_ns": 500, "counts": 5, "mean_ns": 100.0, "min_ns": 1, "max_ns": 2},
    }
    new = {
        "Big": {"total_ns": 9000, "counts": 9, "mean_ns": 1200.0, "min_ns": 1, "max_ns": 2},
        "Small": {"total_ns": 100, "counts": 1, "mean_ns": 100.0, "min_ns": 1, "max_ns": 2},
        "Fresh": {"total_ns": 700, "counts": 7, "mean_ns": 100.0, "min_ns": 1, "max_ns": 2},
    }
    mod.print_comparison(ref, new, top_n=10)
    out = capsys.readouterr().out
    assert out.index("Big") < out.index("Small")  # sorted by total_ns desc
    assert "ONLY in new run" in out and "Fresh" in out
    assert "disappeared" in out and "Gone" in out
    assert "+20.0%" in out  # Big mean 1000 -> 1200


def test_main_missing_file_returns_1(mod, monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", ["prog", str(tmp_path / "nope1.tsv"), str(tmp_path / "nope2.tsv")])
    assert mod.main() == 1


def test_main_happy_path_returns_0(mod, monkeypatch, tmp_path, capsys):
    a = _write(tmp_path / "ref.tsv", [("ZoneA", 1000, 10, 100.0, 5, 200)])
    b = _write(tmp_path / "new.tsv", [("ZoneA", 1000, 10, 110.0, 5, 200)])
    monkeypatch.setattr("sys.argv", ["prog", a, b, "--top", "5"])
    assert mod.main() == 0
    assert "ZoneA" in capsys.readouterr().out

import sys
from pathlib import Path

ROOT = Path(__file__).joinpath("..", "..", "..", "..", "..").resolve()
sys.path.append(str(ROOT / "tools/ci/check_app_version_locks"))

import check_app_version_locks


def test_check_app_version_lock():
    # Keep the spaces to see the difference easily.
    # fmt: off
    app1 = check_app_version_locks.App("app1", set(["a", "b",           "e", "f", "g", "h",         "k"]), set())
    app2 = check_app_version_locks.App("app2", set(["a", "b", "c",      "e",      "g", "h"             ]), set())
    app3 = check_app_version_locks.App("app3", set(["a",      "c", "d", "e",      "g", "h"             ]), set())
    lock = check_app_version_locks.App("lock", set([                    "e",      "g",     "i", "j"    ]), set())
    actual = check_app_version_locks._check_app_version_locks([app1, app2, app3], lock)

    expected = [
        (("app1", "app2", "app3"), ["a", "h"]),
        (("app1", "app2"),         ["b",]),
        (("app2", "app3"),         ["c",]),
        (("app1",),                ["f", "k",]),
        (("app3",),                ["d",]),
    ]
    # fmt: on
    assert len(actual.missings) == len(expected)
    for a, e in zip(actual.missings, expected):
        assert a[0] == e[0]
        assert a[1] == e[1]

    assert len(actual.redundants) == 2
    assert actual.redundants == ["i", "j"]

"""Unit tests for the reusable Isaac Sim design-system parsers.

The directives are exercised end-to-end during the docs build, but the
build only covers the happy path. These tests pin down the parser
contracts so malformed input fails locally with a clear message rather
than only surfacing during a slow Sphinx run.

Run with::

    PYTHONPATH=docs/conf/ext python3 -m pytest -v \\
        docs/conf/ext/isaacsim_design/tests/test_parsers.py

GitLab CI runs the same command on every merge request via the
``test-docs-isaacsim-design`` job in ``.gitlab-ci.yml``.

Page-specific parsers live alongside their owning package; see
``docs/conf/ext/isaacsim_homepage/tests/test_parsers.py``.
"""

from __future__ import annotations

import pytest

from ..links import is_external, resolve_internal_docname

# ---------------------------------------------------------------------------
# links.resolve_internal_docname / is_external
# ---------------------------------------------------------------------------


SOURCE = "isaacsim/index"


def test_links_relative_path() -> None:
    assert resolve_internal_docname("robot_setup/index.html", source_docname=SOURCE) == "isaacsim/robot_setup/index"


def test_links_absolute_path() -> None:
    assert resolve_internal_docname("/installation/index.html", source_docname=SOURCE) == "installation/index"


def test_links_strips_query_and_fragment() -> None:
    assert resolve_internal_docname("gui/index.html#anchor?x=1", source_docname=SOURCE) == "isaacsim/gui/index"


def test_links_path_without_html_extension() -> None:
    assert resolve_internal_docname("gui/index", source_docname=SOURCE) == "isaacsim/gui/index"


def test_links_protocol_relative_url_treated_as_external() -> None:
    # //cdn.example.com/foo inherits the page's scheme. is_external must
    # return True so the validator skips it; otherwise the link would
    # fall through to docname resolution and fail.
    assert is_external("//cdn.example.com/foo") is True
    assert is_external("//example.com/path?x=1") is True
    # Sanity check that single-slash absolute paths stay internal.
    assert is_external("/installation/index.html") is False

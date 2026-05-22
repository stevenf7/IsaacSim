"""Unit tests for the Isaac Sim homepage-specific helpers.

After the homepage refactor, ``isaacsim_homepage`` no longer ships
content directives — the hero, platform diagram, ecosystem tab-set, and
open-source banner are inlined as ``.. raw:: html`` in
``docs/isaacsim/overview/overview.rst``. The only unit-testable surface
left in this package is ``raw_link_check._HREF_RE``, which the
post-parse link checker uses to find ``<a href>`` URLs in raw-HTML
blocks on the master doc.

Run with::

    PYTHONPATH=docs/conf/ext python3 -m pytest -v \\
        docs/conf/ext/isaacsim_homepage/tests/test_parsers.py

GitLab CI runs the same command on every merge request via the
``test-docs-isaacsim-design`` job in ``.gitlab-ci.yml``.

Reusable design-system parsers are tested separately; see
``docs/conf/ext/isaacsim_design/tests/test_parsers.py``.
"""

from __future__ import annotations

from ..raw_link_check import _HREF_RE

# ---------------------------------------------------------------------------
# raw_link_check._HREF_RE
# ---------------------------------------------------------------------------


def test_href_regex_basic_double_quoted() -> None:
    match = _HREF_RE.search('<a href="installation/index.html">Install</a>')
    assert match is not None
    assert match.group("url") == "installation/index.html"


def test_href_regex_basic_single_quoted() -> None:
    match = _HREF_RE.search("<a href='installation/index.html'>Install</a>")
    assert match is not None
    assert match.group("url") == "installation/index.html"


def test_href_regex_double_quoted_url_can_contain_apostrophe() -> None:
    # Regression: an earlier version of the regex used [^"\']+ which
    # would stop matching at the apostrophe even though the href is
    # delimited by double quotes.
    match = _HREF_RE.search("""<a href="page?name=O'Brien">x</a>""")
    assert match is not None
    assert match.group("url") == "page?name=O'Brien"


def test_href_regex_single_quoted_url_can_contain_double_quote() -> None:
    match = _HREF_RE.search("""<a href='page?title="Hi"'>x</a>""")
    assert match is not None
    assert match.group("url") == 'page?title="Hi"'

"""Validate `<a href>` URLs that appear in raw-HTML blocks.

Sphinx's link checker only sees references that are real docutils
reference nodes; an `<a>` written inside a `.. raw:: html` block is
opaque markup that flows straight to the output. This extension walks
the master doc's doctree after parse, finds raw HTML blocks, regexes
out their hrefs, and validates every internal one against the build's
known docnames using the same helper the directives use.

Scoped to the master doc deliberately: the homepage mixes raw HTML
with directive-managed content, so the check pairs with the directive
validators to give the master doc full coverage. Other source files in
this codebase carry pre-existing raw-HTML links that are out of scope
for this MR.

Hooked into `env-check-consistency` so the check runs once per build
after every source file has been read.
"""

from __future__ import annotations

import re
from typing import Any, Final

from docutils import nodes  # type: ignore[import-untyped]
from isaacsim_design.links import validate_internal_link
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment

# The url group uses a negative lookahead against the named opening
# quote rather than `[^"\']+` so an href delimited by one quote style
# can still contain the other (e.g. `href="page?name=O'Brien"`).
_HREF_RE: Final[re.Pattern[str]] = re.compile(
    r'<a\s[^>]*\bhref=(?P<quote>["\'])(?P<url>(?:(?!(?P=quote)).)+)(?P=quote)',
    re.IGNORECASE,
)


def _check_doc(env: BuildEnvironment, docname: str) -> None:
    doctree = env.get_doctree(docname)
    for raw_node in doctree.findall(nodes.raw):
        if raw_node.get("format") != "html":
            continue
        for match in _HREF_RE.finditer(raw_node.astext()):
            href = match.group("url")
            try:
                validate_internal_link(env, href, source_docname=docname)
            except ValueError as exc:
                raise ValueError(f"{docname}: raw HTML link is broken: {exc}") from None


def _on_env_check_consistency(app: Sphinx, env: BuildEnvironment) -> None:
    master = env.config.master_doc
    if master in env.found_docs:
        _check_doc(env, master)


def setup(app: Sphinx) -> dict[str, Any]:
    app.connect("env-check-consistency", _on_env_check_consistency)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

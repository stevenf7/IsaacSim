"""Validate internal hrefs emitted by Isaac Sim docs directives.

Directives emit raw ``<a href>`` strings that Sphinx's link checker
never sees. ``validate_internal_link`` resolves internal hrefs against
the build's known docs and raises when the target is missing.
"""

from __future__ import annotations

from posixpath import dirname, join, normpath
from typing import Final

from sphinx.environment import BuildEnvironment

# `//` covers protocol-relative URLs which inherit the page's scheme
# and would otherwise fall through to internal docname resolution.
_EXTERNAL_PREFIXES: Final[tuple[str, ...]] = ("http://", "https://", "mailto:", "tel:", "//")


def is_external(href: str) -> bool:
    return href.startswith(_EXTERNAL_PREFIXES)


def _strip_query_fragment(href: str) -> str:
    return href.split("#", 1)[0].split("?", 1)[0]


def resolve_internal_docname(href: str, *, source_docname: str) -> str:
    """Translate an internal href into a Sphinx docname.

    A leading ``/`` makes the path absolute from the project root;
    otherwise it resolves relative to ``source_docname``'s directory.
    """
    path = _strip_query_fragment(href)
    if path.endswith(".html"):
        path = path[:-5]
    if path.startswith("/"):
        return path.lstrip("/")
    return normpath(join(dirname(source_docname), path))


def validate_internal_link(
    env: BuildEnvironment,
    href: str,
    *,
    source_docname: str | None = None,
) -> None:
    """Raise ValueError if ``href`` is internal and doesn't resolve to a known doc."""
    if is_external(href):
        return
    if not href or href.startswith("#"):
        return
    if source_docname is None:
        source_docname = getattr(env, "docname", None) or env.config.master_doc
    docname = resolve_internal_docname(href, source_docname=source_docname)
    if docname not in env.found_docs:
        raise ValueError(f"link target not found: {href!r} " f"(resolved to docname {docname!r})")

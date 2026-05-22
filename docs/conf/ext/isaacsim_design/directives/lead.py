"""`isaacsim-lead::` Sphinx directive.

Wraps a paragraph in `<p class="isaacsim-section-lead">`. Use it to
introduce a docs section with one concise sentence of context. RST inline
markup in the body (e.g.
``**Quick Install**``) is parsed normally.

Example::

   .. isaacsim-lead::

      Pick the setup that matches how you work. Most users should
      start with **Quick Install**.
"""

from __future__ import annotations

from typing import Any, ClassVar

from docutils import nodes  # type: ignore[import-untyped]
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective


class IsaacSimLead(SphinxDirective):
    """Render a section-lead paragraph."""

    has_content: ClassVar[bool] = True
    required_arguments: ClassVar[int] = 0
    optional_arguments: ClassVar[int] = 0

    def run(self) -> list[nodes.Node]:
        if not any(line.strip() for line in self.content):
            raise self.error("isaacsim-lead: body text is required")

        container = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, container)

        # Reject anything that is not exactly one paragraph: lists,
        # admonitions, code blocks, etc. would otherwise be silently
        # dropped or render with the wrong styling.
        non_paragraph = [type(child).__name__ for child in container.children if not isinstance(child, nodes.paragraph)]
        if non_paragraph:
            raise self.error(
                "isaacsim-lead: body must be a single paragraph (no lists, "
                f"admonitions, or code blocks); found {non_paragraph}"
            )
        paragraphs = [child for child in container.children if isinstance(child, nodes.paragraph)]
        if not paragraphs:
            raise self.error("isaacsim-lead: body must contain a paragraph")
        if len(paragraphs) > 1:
            raise self.error("isaacsim-lead: body must be exactly one paragraph; " f"found {len(paragraphs)}")

        paragraph = paragraphs[0]
        paragraph["classes"].append("isaacsim-section-lead")
        return [paragraph]


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_directive("isaacsim-lead", IsaacSimLead)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

"""`isaacsim-difficulty::` Sphinx directive.

Renders a Beginner / Intermediate / Advanced banner above any grouped
learning content. The single argument names the level; the body holds
the explanatory text and accepts RST inline markup (``**bold**``, etc.).

Example::

   .. isaacsim-difficulty:: beginner

      Learn the app, scenes, and **core** robot workflows
"""

from __future__ import annotations

from typing import Any, ClassVar, Final

from docutils import nodes  # type: ignore[import-untyped]
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

_LEVELS: Final[tuple[str, ...]] = ("beginner", "intermediate", "advanced")


class IsaacSimDifficulty(SphinxDirective):
    """Render a difficulty banner."""

    has_content: ClassVar[bool] = True
    required_arguments: ClassVar[int] = 1
    optional_arguments: ClassVar[int] = 0
    final_argument_whitespace: ClassVar[bool] = False

    def run(self) -> list[nodes.Node]:
        level: str = self.arguments[0].strip().lower()
        if level not in _LEVELS:
            raise self.error(f"isaacsim-difficulty: unknown level {level!r}. " f"Choose one of: {', '.join(_LEVELS)}")
        if not any(line.strip() for line in self.content):
            raise self.error("isaacsim-difficulty: body text is required")

        # Parse the body so RST inline markup (e.g. **bold**) renders
        # as proper docutils nodes rather than literal text.
        parsed = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, parsed)
        paragraphs = [child for child in parsed.children if isinstance(child, nodes.paragraph)]
        if not paragraphs:
            raise self.error("isaacsim-difficulty: body must contain a paragraph")
        if len(paragraphs) > 1:
            raise self.error("isaacsim-difficulty: body must be exactly one paragraph; " f"found {len(paragraphs)}")

        banner = nodes.container()
        banner["classes"] = ["isaacsim-diff", f"isaacsim-diff--{level}"]

        badge = nodes.inline(text=level.capitalize())
        badge["classes"] = ["isaacsim-diff__badge"]
        banner += badge

        text_inline = nodes.inline()
        text_inline["classes"] = ["isaacsim-diff__text"]
        text_inline += paragraphs[0].children
        banner += text_inline

        return [banner]


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_directive("isaacsim-difficulty", IsaacSimDifficulty)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

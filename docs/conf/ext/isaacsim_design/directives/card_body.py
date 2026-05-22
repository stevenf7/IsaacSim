"""`isaacsim-card-body::` Sphinx directive.

Renders a reusable icon/title/description/meta block for use inside
sphinx-design `grid-item-card` containers. The outer card (link, hover,
layout) is owned by sphinx-design; this directive only emits the body.

Example::

   .. grid-item-card::
      :link: isaac_sim_quick_install
      :link-type: ref
      :class-card: isaacsim-doc-card

      .. isaacsim-card-body::
         :icon: bolt
         :title: Quick Install
         :desc: Fastest path to a working local setup.
"""

from __future__ import annotations

from html import escape
from typing import Any, ClassVar, Final

from docutils import nodes  # type: ignore[import-untyped]
from docutils.parsers.rst import Directive, directives  # type: ignore[import-untyped]
from sphinx.application import Sphinx

from ..icons import render_in_circle

_ICON_SIZE: Final[int] = 26


class IsaacSimCardBody(Directive):
    """Render an Isaac Sim docs card body."""

    has_content: ClassVar[bool] = False
    required_arguments: ClassVar[int] = 0
    optional_arguments: ClassVar[int] = 0
    final_argument_whitespace: ClassVar[bool] = False

    option_spec = {
        "icon": directives.unchanged_required,
        "title": directives.unchanged_required,
        "desc": directives.unchanged_required,
        "meta": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        icon_name: str = self.options["icon"]
        try:
            icon_html = render_in_circle(icon_name, size=_ICON_SIZE)
        except KeyError as exc:
            raise self.error(f"isaacsim-card-body: {exc}") from None

        title = escape(self.options["title"])
        desc = escape(self.options["desc"])
        meta = self.options.get("meta", "").strip()

        parts: list[str] = [
            icon_html,
            f'<div class="isaacsim-card-title isaacsim-title-sm">{title}</div>',
            f'<div class="isaacsim-card-desc isaacsim-copy-sm">{desc}</div>',
        ]
        if meta:
            parts.append(
                f'<div class="isaacsim-card-meta isaacsim-meta">' f"<strong>Best for:</strong> {escape(meta)}" f"</div>"
            )

        return [nodes.raw("", "\n".join(parts), format="html")]


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_directive("isaacsim-card-body", IsaacSimCardBody)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

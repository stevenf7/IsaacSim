"""`isaacsim-link-grid::` — grid of icon links, one ``icon | href | name | desc`` per body line.

Example::

   .. isaacsim-link-grid::

      speech         | https://forums.developer.nvidia.com/c/omniverse/simulation/69 | Forum         | Ask questions and get help.
      external-link  | https://discord.gg/4ZsTFksGh8                                  | Discord       | Chat in real time.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any, ClassVar, Final

from docutils import nodes  # type: ignore[import-untyped]
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

from ..icons import render as render_icon
from ..links import validate_internal_link

_FIELD_SEPARATOR: Final[str] = "|"
_ICON_SIZE: Final[int] = 24


@dataclass(frozen=True, slots=True)
class _Card:
    """A single icon-link card row."""

    icon: str
    href: str
    name: str
    desc: str


def _parse_cards(content: list[str]) -> list[_Card]:
    cards: list[_Card] = []
    for raw_line in content:
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(_FIELD_SEPARATOR)]
        if len(parts) != 4:
            raise ValueError(f"each line must be 'icon | href | name | desc', got: {line!r}")
        icon, href, name, desc = parts
        cards.append(_Card(icon=icon, href=href, name=name, desc=desc))
    return cards


def _is_external(href: str) -> bool:
    return href.startswith(("http://", "https://"))


def _render_card(card: _Card) -> str:
    target_attrs = ' target="_blank" rel="noopener noreferrer"' if _is_external(card.href) else ""
    icon_svg = render_icon(card.icon, size=_ICON_SIZE)
    return (
        f'<a href="{escape(card.href, quote=True)}" '
        f'class="isaacsim-link-card isaacsim-surface isaacsim-surface--interactive"{target_attrs}>'
        f'<div class="isaacsim-link-card__icon isaacsim-marker isaacsim-marker--icon">{icon_svg}</div>'
        f'<div class="isaacsim-link-card__title isaacsim-title-sm">{escape(card.name)}</div>'
        f'<div class="isaacsim-link-card__copy isaacsim-copy-sm">{escape(card.desc)}</div>'
        "</a>"
    )


class IsaacSimLinkGrid(SphinxDirective):
    """Render a reusable icon-link grid."""

    has_content: ClassVar[bool] = True
    required_arguments: ClassVar[int] = 0
    optional_arguments: ClassVar[int] = 0

    def run(self) -> list[nodes.Node]:
        try:
            cards = _parse_cards(list(self.content))
        except ValueError as exc:
            raise self.error(f"isaacsim-link-grid: {exc}") from None
        if not cards:
            raise self.error("isaacsim-link-grid: at least one card is required")
        for card in cards:
            # Link cards must point somewhere; an empty or pure
            # `#` href would render a clickable card that goes nowhere.
            # The shared validator only rejects unknown internal docs,
            # so we add the stricter check here at the call site.
            if not card.href or card.href.startswith("#"):
                raise self.error(
                    f"isaacsim-link-grid: card {card.name!r}: " f"href is empty or anchor-only ({card.href!r})"
                )
            try:
                validate_internal_link(self.env, card.href)
            except ValueError as exc:
                raise self.error(f"isaacsim-link-grid: card {card.name!r}: {exc}") from None
        try:
            cards_html = "".join(_render_card(card) for card in cards)
        except KeyError as exc:
            raise self.error(f"isaacsim-link-grid: {exc}") from None

        html = f'<div class="isaacsim-link-grid isaacsim-grid isaacsim-grid--4">{cards_html}</div>'
        return [nodes.raw("", html, format="html")]


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_directive("isaacsim-link-grid", IsaacSimLinkGrid)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

"""SVG icon registry shared by the ``card_body`` and ``link_grid`` directives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

_STROKE_BASE: Final[str] = (
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"'
)


def _stroke(width: float = 1.5) -> str:
    return f'{_STROKE_BASE} stroke-width="{width}"'


@dataclass(frozen=True, slots=True)
class Icon:
    """``attrs`` go on the outer ``<svg>``; ``inner`` is the children markup."""

    attrs: str
    inner: str


_ICONS: Final[dict[str, Icon]] = {
    "bolt": Icon(
        attrs=_stroke(),
        inner='<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    ),
    "monitor": Icon(
        attrs=_stroke(),
        inner=(
            '<rect x="2" y="3" width="20" height="14" rx="2"/>'
            '<line x1="8" y1="21" x2="16" y2="21"/>'
            '<line x1="12" y1="17" x2="12" y2="21"/>'
        ),
    ),
    "cube": Icon(
        attrs=_stroke(),
        inner=(
            '<path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/>'
            '<polyline points="3.27 6.96 12 12.01 20.73 6.96"/>'
            '<line x1="12" y1="22.08" x2="12" y2="12"/>'
        ),
    ),
    "prompt": Icon(
        attrs=_stroke(),
        inner='<polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>',
    ),
    "speech": Icon(
        attrs=_stroke(),
        inner='<path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>',
    ),
    "external-link": Icon(
        attrs=_stroke(),
        inner=(
            '<path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/>'
            '<polyline points="15 3 21 3 21 9"/>'
            '<line x1="10" y1="14" x2="21" y2="3"/>'
        ),
    ),
    "doc": Icon(
        attrs=_stroke(),
        inner=(
            '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>'
            '<path d="M14 2v6h6"/>'
            '<path d="M8 13h8"/>'
            '<path d="M8 17h5"/>'
        ),
    ),
    "help": Icon(
        attrs=_stroke(),
        inner=(
            '<circle cx="12" cy="12" r="10"/>' '<path d="M9.09 9a3 3 0 115.82 1c0 2-3 3-3 3"/>' '<path d="M12 17h.01"/>'
        ),
    ),
}


def get(name: str) -> Icon:
    try:
        return _ICONS[name]
    except KeyError:
        raise KeyError(f"Unknown icon {name!r}. Known: {', '.join(sorted(_ICONS))}") from None


def render(name: str, *, size: int) -> str:
    """Render the icon as an ``<svg>`` string at the requested pixel size."""
    icon = get(name)
    return f'<svg aria-hidden="true" {icon.attrs} width="{size}" height="{size}">{icon.inner}</svg>'


def render_in_circle(
    name: str,
    *,
    size: int,
    circle_class: str = "isaacsim-card-icon__circle",
    wrapper_class: str = "isaacsim-card-icon",
) -> str:
    """Render the icon wrapped in the standard circle markup."""
    return f'<div class="{wrapper_class}"><div class="{circle_class}">{render(name, size=size)}</div></div>'

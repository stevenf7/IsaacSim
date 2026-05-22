"""Register the shared ``isaacsim-design.css`` stylesheet on every page."""

from __future__ import annotations

from typing import Any

from sphinx.application import Sphinx
from sphinx.config import Config

_DESIGN_STATIC_PATH = "design_static"
_DESIGN_CSS = "isaacsim-design.css"


def _on_config_inited(app: Sphinx, config: Config) -> None:
    if _DESIGN_STATIC_PATH not in config.html_static_path:
        config.html_static_path.append(_DESIGN_STATIC_PATH)


def setup(app: Sphinx) -> dict[str, Any]:
    # priority=900 loads after sphinx-design + theme CSS so these
    # primitives can safely refine sphinx-design components.
    app.add_css_file(_DESIGN_CSS, priority=900)
    app.connect("config-inited", _on_config_inited)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

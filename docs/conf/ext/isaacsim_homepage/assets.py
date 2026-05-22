"""Register homepage CSS + hero image; scope the bundle to the master doc."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.errors import ExtensionError

_HOMEPAGE_STATIC_PATH = "homepage_static"
_HOMEPAGE_CSS = "isaacsim-homepage.css"
# Multiple formats so the CSS image-set() rule can pick the best per browser.
_HERO_IMAGE_FILES: Final[tuple[str, ...]] = (
    "isim_6.0_full_ref_viewport_hero_shot.png",
    "isim_6.0_full_ref_viewport_hero_shot.webp",
)
# Anchored on __file__ rather than app.srcdir because repo_docs sets srcdir
# to docs/isaacsim, not the top-level docs/ folder.
_HERO_IMAGE_SOURCE_DIR: Final[Path] = Path(__file__).resolve().parents[3] / "isaacsim" / "images"


def _asset_name(entry: Any) -> str:
    if isinstance(entry, str):
        return entry
    # pydata-sphinx-theme uses (filename, attrs) tuples; Sphinx >=4 uses
    # _CssFile / _JavaScript objects with a filename-like attr.
    if isinstance(entry, (tuple, list)) and entry:
        first = entry[0]
        return first if isinstance(first, str) else ""
    return getattr(entry, "filename", None) or getattr(entry, "src", None) or ""


def _drop_asset(items: list[Any], target: str) -> list[Any]:
    # Match on basename only so we don't also drop sourcemap siblings.
    kept: list[Any] = []
    for item in items:
        name = _asset_name(item)
        basename = name.rsplit("/", 1)[-1] if name else ""
        if basename != target:
            kept.append(item)
    return kept


def _on_config_inited(app: Sphinx, config: Config) -> None:
    if _HOMEPAGE_STATIC_PATH not in config.html_static_path:
        config.html_static_path.append(_HOMEPAGE_STATIC_PATH)


def _on_html_page_context(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, Any],
    doctree: Any,
) -> None:
    if pagename == app.config.master_doc:
        return
    if "css_files" in context:
        context["css_files"] = _drop_asset(context["css_files"], _HOMEPAGE_CSS)


def _on_build_finished(app: Sphinx, exception: BaseException | None) -> None:
    """Copy hero image files into the build's _static directory.

    Raises ExtensionError if a file is missing or is an unresolved LFS
    pointer — both render as a broken hero, so fail loudly at build time.
    """
    if exception is not None or app.builder.name != "html":
        return
    dst_dir = Path(app.outdir) / "_static"
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name in _HERO_IMAGE_FILES:
        src = _HERO_IMAGE_SOURCE_DIR / name
        if not src.is_file():
            raise ExtensionError(f"hero asset missing: {src}")
        data = src.read_bytes()
        if data[:40].startswith(b"version https://git-lfs."):
            raise ExtensionError(
                f"hero asset {src} is an unresolved Git-LFS pointer " f"({len(data)} bytes); run `git lfs pull`."
            )
        (dst_dir / name).write_bytes(data)


def setup(app: Sphinx) -> dict[str, Any]:
    # priority=910 loads after isaacsim_design.tokens (900) so this can
    # refine the shared primitives without specificity wars.
    app.add_css_file(_HOMEPAGE_CSS, priority=910)
    app.connect("config-inited", _on_config_inited)
    app.connect("html-page-context", _on_html_page_context)
    app.connect("build-finished", _on_build_finished)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

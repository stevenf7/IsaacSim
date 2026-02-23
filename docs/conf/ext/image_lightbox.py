"""Sphinx extension: image lightbox with keyboard/swipe carousel.

Registers a CSS file and a JS file that together turn every content image
into a clickable lightbox.  Left/Right arrows (and touch swipe) cycle
through all images on the page.  Escape or clicking the backdrop closes
the overlay.  Small inline icons (<=40 px) are excluded automatically.

The extension copies its assets to ``_static/`` during ``build-finished``
so it works regardless of which build driver is used.
"""

import os
import shutil


def _copy_assets(app, exception):
    if exception:
        return
    conf_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_dir = os.path.join(app.outdir, "_static")
    os.makedirs(static_dir, exist_ok=True)
    for name in ("image_lightbox.css", "image_lightbox.js"):
        src = os.path.join(conf_dir, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(static_dir, name))


def setup(app):
    app.add_css_file("image_lightbox.css")
    app.add_js_file("image_lightbox.js")
    app.connect("build-finished", _copy_assets)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import platform
import omni.kit.pipapi

import omni.isaac
import omni.kit.commands


omni.kit.pipapi.install("numpy")
# -- Project information -----------------------------------------------------

project = "Omniverse Robotics"
copyright = "2020, NVIDIA."
author = "NVIDIA"
version = "2020.2"
release = version

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.intersphinx", "sphinx.ext.todo"]

todo_include_todos = True

autodoc_default_options = {"show-inheritance": True}
autodoc_mock_imports = ["PIL", "matplotlib", "torch"]

autoclass_content = "both"

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
import sphinx_rtd_theme

html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_theme = "sphinx_rtd_theme"

# html_theme = 'alabaster'
html_logo = "content/robotics_logo_square.png"

html_theme_options = {
    "logo_only": True,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "style_nav_header_background": "#000000",
    # Toc options
    "collapse_navigation": False,
    "sticky_navigation": False,
    # 'navigation_depth': 10,
    "includehidden": True,
    "titles_only": False,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["pk_scripts.js"]

html_last_updated_fmt = ""


def setup(app):
    app.add_css_file("custom.css")


html_js_files = ["pk_scripts.js"]

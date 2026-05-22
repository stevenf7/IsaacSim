"""Reusable, page-agnostic Sphinx contributions for the Isaac Sim docs.

Modules: ``tokens`` (CSS bundle), ``icons`` (SVG registry), ``links``
(internal href validator), ``directives/`` (``card_body``, ``difficulty``,
``lead``, ``link_grid``).

Page-specific glue lives in sibling packages such as ``isaacsim_homepage``;
``isaacsim_design`` must not import from them.
"""

"""Page-specific Sphinx hooks for the Isaac Sim documentation homepage.

* ``assets`` — registers the homepage CSS, copies the hero image into
  ``_static/``, scopes the bundle so non-homepage builds skip it.
* ``raw_link_check`` — validates ``<a href>`` URLs that appear inside
  ``.. raw:: html`` blocks on the master doc.

Page content (hero, platform diagram, ecosystem tab-set, open-source
banner) is inlined as ``.. raw:: html`` in
``docs/isaacsim/overview/overview.rst``.

May import from ``isaacsim_design``; the reverse is forbidden.
"""

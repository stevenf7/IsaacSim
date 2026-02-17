.. ==============================================================================================================
.. THIS PAGE IS AUTO-GENERATED, DO NOT MANUALLY EDIT.
.. Refer to https://gitlab-master.nvidia.com/omniverse/omni-docs/-/wikis/Generate-Node-Documentation for details.
.. ==============================================================================================================

==============================
|omnigraph_short| Node Library
==============================

Here, you can find definitions, descriptions, and examples of |omnigraph_short| nodes. Each |omnigraph_short| node belongs to a category, which is our method of grouping nodes together by function.

{% for name in category_order %}
{{ name }}
{{ "-" * name|length }}

.. toctree::
   :maxdepth: 1
   :glob:
{% for _, filename in category_nodes[name]|sort(attribute="0") %}
   {{ filename }}
{%- endfor %}
{% endfor %}

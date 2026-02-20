.. ==============================================================================================================
.. THIS PAGE IS AUTO-GENERATED, DO NOT MANUALLY EDIT.
.. Refer to https://gitlab-master.nvidia.com/omniverse/omni-docs/-/wikis/Generate-Node-Documentation for details.
.. ==============================================================================================================

.. meta::
   :title: {{ title }}
   :keywords: lang-en {{ keywords }}

{{ "=" * title|length }}
{{ title }}
{{ "=" * title|length }}

{% if image %}
.. image:: /images/{{ image }}
    :align: center
    :width: 800
{% endif %}

{{ description }}

{% if custom_content_pre is defined -%}
.. include:: {{ custom_content_pre }}
{% endif -%}

{% if node_extension %}
Installation
------------

To use this Node, you must enable ``{{ node_extension }}`` in the Extension Manager.
{% endif %}

{% if inputs %}
Inputs
------

.. csv-table::
   :header: "Name", "Type", "Description", "Default"

   {{ inputs }}

{% if input_constraints -%}
**Constraints:**

{% for constraint in input_constraints %}
   - {{ constraint }}
{% endfor %}
{% endif -%}

{% endif %}

{% if outputs %}
Outputs
-------

.. csv-table::
   :header: "Name", "Type", "Description", "Default"

   {{ outputs }}

{% if output_constraints -%}
**Constraints:**

{% for constraint in output_constraints %}
   - {{ constraint }}
{% endfor %}
{% endif -%}

{% endif %}

{% if custom_content_post is defined -%}
.. include:: {{ custom_content_post }}
{% endif -%}


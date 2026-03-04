..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_asset_transformer_api:

Asset Transformer API
=====================

This page covers programmatic usage of the Asset Transformer, including API classes, custom rule development, and integration patterns.

For UI-based usage, refer to :ref:`Asset Transformer <isaac_sim_app_asset_transformer>`. For available rules, review :ref:`Asset Transformer Rules Reference <isaac_sim_app_asset_transformer_rules>`.

Rule Interface
--------------

All transformation rules implement the ``RuleInterface`` abstract base class. This interface defines the contract for rule implementations:

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_rule_interface.png
   :align: center
   :width: 75%
   :alt: Rule Interface Architecture

.. literalinclude:: ../snippets/robot_setup/asset_transformer_api.py
   :start-after: <start-rule-interface-snippet>
   :end-before: <end-rule-interface-snippet>
   :language: python

**Key Methods**:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Method
     - Description
   * - ``process_rule()``
     - Execute the rule logic. Return ``None`` to continue with the current working stage, or return a file path to switch the working stage for subsequent rules.
   * - ``get_configuration_parameters()``
     - Return a list of ``RuleConfigurationParam`` objects describing the rule's configurable parameters.
   * - ``log_operation()``
     - Record human-readable log messages for the execution report.
   * - ``add_affected_stage()``
     - Record identifiers for stages or layers modified by the rule.

Rule Logging
^^^^^^^^^^^^

Every rule implementation must provide adequate logging through the ``log_operation()`` method. This creates a detailed audit trail of transformations:

.. literalinclude:: ../snippets/robot_setup/asset_transformer_api.py
   :start-after: <start-process-rule-logging-snippet>
   :end-before: <end-process-rule-logging-snippet>
   :language: python

**Logging Best Practices**:

- Log the rule start with key configuration parameters
- Log pattern matches and filter criteria
- Log each significant operation (schema moves, property copies, prim transfers)
- Log summary statistics (counts of processed items)
- Log affected stages using ``add_affected_stage()``
- Log completion status

Rule Registration
-----------------

The ``RuleRegistry`` is a singleton class that maintains a mapping of rule type names to their implementation classes. When the ``AssetTransformerManager`` executes a profile, it looks up each rule's ``type`` string in the registry to find the corresponding implementation class.

The ``RuleRegistry`` uses a singleton pattern, meaning there is only one global instance shared across all code. This allows rules registered by any extension or module to be available to all transformation profiles.

**Registry Methods**:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Method
     - Description
   * - ``register(rule_cls)``
     - Register a rule class. The key is computed as ``{module}.{qualname}``. Raises ``TypeError`` if the class does not inherit from ``RuleInterface``.
   * - ``get(rule_type)``
     - Look up a rule class by its fully qualified type name. Returns ``None`` if not found.
   * - ``list_rules()``
     - Return a dictionary mapping all registered type names to their implementation classes.
   * - ``list_rule_types()``
     - Return a sorted list of all registered rule type names.
   * - ``clear()``
     - Remove all registered rules. Primarily used for testing.

Creating Custom Rules
---------------------

To create a custom transformation rule, implement the ``RuleInterface`` abstract base class and register it with the ``RuleRegistry``.

.. dropdown:: Complete Custom Rule Example
   :color: primary
   :open:

   .. literalinclude:: ../snippets/robot_setup/asset_transformer_api.py
      :start-after: <start-custom-rule-example-snippet>
      :end-before: <end-custom-rule-example-snippet>
      :language: python

**Referencing a Custom Rule in a Profile**:

The rule is registered using its fully qualified class name (``{module}.{class_name}``), which becomes the ``type`` string in rule specifications:

.. literalinclude:: ../snippets/robot_setup/asset_transformer_api.py
   :start-after: <start-rule-spec-snippet>
   :end-before: <end-rule-spec-snippet>
   :language: python

Extension-Based Registration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For Isaac Sim extensions, register rules when the extension loads:

.. literalinclude:: ../snippets/robot_setup/asset_transformer_api.py
   :start-after: <start-extension-registration-snippet>
   :end-before: <end-extension-registration-snippet>
   :language: python

Programmatic API Usage
----------------------

The Asset Transformer can be invoked programmatically using the Python API. This enables integration into automated pipelines, batch processing, and custom tooling.

Basic Usage
^^^^^^^^^^^

.. literalinclude:: ../snippets/robot_setup/asset_transformer_api.py
   :start-after: <start-basic-usage-snippet>
   :end-before: <end-basic-usage-snippet>
   :language: python

Loading a Profile from JSON
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/robot_setup/asset_transformer_api.py
   :start-after: <start-load-profile-from-json-snippet>
   :end-before: <end-load-profile-from-json-snippet>
   :language: python

Saving the Execution Report
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/robot_setup/asset_transformer_api.py
   :start-after: <start-save-execution-report-snippet>
   :end-before: <end-save-execution-report-snippet>
   :language: python

Accessing Rule Logs
^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/robot_setup/asset_transformer_api.py
   :start-after: <start-accessing-rule-logs-snippet>
   :end-before: <end-accessing-rule-logs-snippet>
   :language: python

Querying Registered Rules
^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/robot_setup/asset_transformer_api.py
   :start-after: <start-querying-registered-rules-snippet>
   :end-before: <end-querying-registered-rules-snippet>
   :language: python

API Classes Reference
---------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Class
     - Description
   * - ``AssetTransformerManager``
     - Coordinates execution of rule profiles over USD stages. Call ``run()`` to execute a transformation.
   * - ``RuleProfile``
     - Defines a complete transformation pipeline with profile metadata and ordered rule specifications.
   * - ``RuleSpec``
     - Specification for a single rule including name, type, destination, parameters, and enabled state.
   * - ``ExecutionReport``
     - Contains the results of a transformation run including per-rule logs, timestamps, and the output stage path.
   * - ``RuleExecutionResult``
     - Result of executing a single rule including success status, log entries, affected stages, and error information.
   * - ``RuleRegistry``
     - Singleton registry mapping rule type names to implementation classes. Rules are registered automatically when their extensions load.
   * - ``RuleInterface``
     - Abstract base class for all transformation rules. Implement this to create custom rules.
   * - ``RuleConfigurationParam``
     - Describes a configurable parameter for a rule, including name, type, default value, and description.

Error Handling
--------------

.. literalinclude:: ../snippets/robot_setup/asset_transformer_api.py
   :start-after: <start-error-handling-snippet>
   :end-before: <end-error-handling-snippet>
   :language: python

**Common Errors**:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Error
     - Cause
   * - ``RuntimeError: Failed to open source stage``
     - The input USD file does not exist or is corrupted
   * - ``RuntimeError: Failed to export base stage``
     - Cannot write to the output directory (permissions, disk full)
   * - ``TypeError: rule_cls must subclass RuleInterface``
     - Attempting to register a class that does not inherit from ``RuleInterface``
   * - Rule ``error`` field populated
     - Exception raised during ``process_rule()`` execution


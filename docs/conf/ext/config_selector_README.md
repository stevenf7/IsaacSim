---
orphan: true
---

# Configuration Selector Extension

This Sphinx extension provides a reusable alternative to nested tabs. Authors define a single selector with semantic RST options, then wrap page sections in `config-content` blocks. The extension owns the generated HTML, shared CSS, JavaScript behavior, URL synchronization, and scope handling.

## Installation

1. Add the extension to your Sphinx configuration:

```python
# In conf.py
extensions = [
    # ... other extensions
    "config_selector",
]
```

2. Ensure the extension file `config_selector.py` is in the `docs/conf/ext/` directory. The extension registers `docs/isaacsim/design_static/` and `isaacsim-config-selector.js` automatically; page authors do not need to add static assets in `conf.py`.

## Usage

### Configuration Selector

Add a configuration selector near the top of your page:

```rst
.. config-selector::
   :title: Build Environment
   :scope: setup
   :persist: session
   :persist-key: ros2
   :options: platform=Ubuntu 22.04|Ubuntu 24.04|Windows,ros_distro=Humble|Jazzy,package_type=Default|Custom
   :dependencies: ros_distro=platform:Ubuntu 22.04;package_type:Default
```

**Selector Options:**

- `:title:` sets the visible heading in the selector banner. Defaults to `Configuration`.
- `:scope:` namespaces generated IDs, content blocks, and URL parameters. Defaults to `default`.
- `:options:` uses `key=value1|value2|value3` groups separated by commas.
- `:dependencies:` hides selector rows until other choices match. Use `row_key=dependency_key:dependency_value`; separate multiple conditions for the same row with semicolons, for example `mode=platform:Linux;edition:Advanced`.
- `:persist:` is optional. Set it to `session` to remember selections for same-tab navigation.
- `:persist-key:` names the session persistence group. Selectors with the same key share compatible option values. Defaults to the selector scope.

Use a unique `:scope:` for each selector on a page. If two selectors in one document use the same scope, the build emits a warning because the selectors would share HTML IDs and URL parameters.

The selector renders as a sticky banner that pins below the NVIDIA/PyData top navigation. It uses shared styles from `isaacsim-design.css` and Bootstrap/PyData theme variables.

### Conditional Content

Wrap content that should be conditionally displayed:

```rst
.. config-content::
   :scope: setup
   :show-when: platform=Ubuntu 22.04,ros_distro=Humble

   This content only appears when Ubuntu 22.04 and Humble are selected.

   .. code-block:: bash

      sudo apt install ros-humble-desktop
```

**Content Options:**

- `:show-when:` uses `key=value,key2=value2`; all conditions must match for content to be displayed.
- `:scope:` is optional. If omitted, the block inherits the most recently parsed `config-selector` scope in the same document. Add `:scope:` explicitly when a page has more than one selector or when content is far from its selector.

## Linkable Configurations

Selections are synchronized to query parameters so users can copy a URL for a specific configuration. The default scope writes plain keys, for example `?platform=Linux`. Named scopes prefix keys, for example `?setup.platform=Linux&setup.ros_distro=Jazzy`.

URL parameters are canonical: if a URL contains selector parameters, the selector reads them during initialization and normalizes the visible configuration back into the URL. For selectors with `:persist: session`, a page with no selector parameters restores matching values from `sessionStorage` when the current selector uses the same `:persist-key:` and supports those values, then writes the restored state into the destination page URL. A first page load with no stored selection keeps the URL clean.

## Examples

### Basic Example

```rst
Configuration Selector Demo
===========================

Select your configuration:

.. config-selector::
   :scope: install
   :options: os=Linux|Windows,version=22.04|24.04

Installation Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^

.. config-content::
   :scope: install
   :show-when: os=Linux,version=22.04

   **Linux 22.04 Installation**

   .. code-block:: bash

      sudo apt update
      sudo apt install package-name

.. config-content::
   :scope: install
   :show-when: os=Windows

   **Windows Installation**

   .. code-block:: bash

      # Use WSL2
      wsl --install
```

### Row Dependencies

```rst
.. config-selector::
   :title: ROS Setup
   :scope: setup
   :persist: session
   :persist-key: ros2
   :options: platform=Ubuntu 22.04|Ubuntu 24.04|Windows,ros_distro=Humble|Jazzy,package_type=Default|Custom
   :dependencies: ros_distro=platform:Ubuntu 22.04;package_type:Default

.. config-content::
   :scope: setup
   :show-when: platform=Ubuntu 22.04,ros_distro=Humble,package_type=Default

   **Ubuntu 22.04 + Humble + Default Configuration**

   Specific instructions for this exact combination.

.. config-content::
   :scope: setup
   :show-when: platform=Windows

   **Windows Configuration**

   This appears for Windows regardless of other selections.
```

## Technical Details

### Components

1. **ConfigSelectorDirective**:
   - Parses configuration options.
   - Renders the HTML selector widget.
   - Registers shared static assets.

2. **ConfigContentDirective**:
   - Wraps conditional content.
   - Stores show-when conditions as data attributes.

3. **Static assets**:
   - `docs/isaacsim/design_static/isaacsim-design.css` owns the selector styling.
   - `docs/isaacsim/design_static/isaacsim-config-selector.js` owns row visibility, content visibility, layout offsets, URL synchronization, and opt-in session persistence.

## Customization

### Styling

Prefer the existing theme and design-system classes before adding selector-specific CSS. The selector buttons use Bootstrap button classes and are themed through `--bs-btn-*` variables and PyData/NVIDIA theme tokens in `isaacsim-design.css`.

Useful classes:

```css
.config-selector {
    /* Sticky selector container */
}

.config-options {
    /* Rows of selector controls */
}

.config-btn {
    /* Bootstrap-backed selector buttons */
}
```

## Troubleshooting

### Content Not Showing/Hiding

- Check that `:show-when:` conditions exactly match selector values.
- Check that the `config-content` scope matches its selector scope.
- Use unique selector scopes when there is more than one selector on a page.
- Ensure JavaScript is enabled.
- Verify no syntax errors in configuration strings.

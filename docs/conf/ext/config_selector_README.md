---
orphan: true
---

# Configuration Selector Extension

This Sphinx extension provides an alternative to nested tabs by implementing a configuration selector. Users select their configuration once at the top of the page, and all relevant content is dynamically shown/hidden throughout the document.

## Installation

1. Add the extension to your Sphinx configuration:

```python
# In conf.py
extensions = [
    # ... other extensions
    'config_selector',
]
```

2. Ensure the extension file `config_selector.py` is in the `docs/conf/ext/` directory.

## Usage

### Configuration Selector

Add a configuration selector at the top of your page:

```rst
.. config-selector::
   :options: platform=Ubuntu 22.04|Ubuntu 24.04|Windows,ros_distro=Humble|Jazzy,package_type=Default|Custom
```

**Options Format:**
- `key=value1|value2|value3` - Define configuration keys with possible values
- Multiple keys separated by commas
- Values separated by pipes (`|`)

The selector renders as a sticky banner that pins to the top of the viewport as the user scrolls, with a compact horizontal layout and a collapse toggle.

### Conditional Content

Wrap content that should be conditionally displayed:

```rst
.. config-content::
   :show-when: platform=Ubuntu 22.04,ros_distro=Humble
   
   This content only appears when Ubuntu 22.04 and Humble are selected.
   
   .. code-block:: bash
   
       sudo apt install ros-humble-desktop
```

**Show-When Format:**
- `key=value,key2=value2` - Define conditions for showing content
- All conditions must match for content to be displayed
- Conditions separated by commas

## Examples

### Basic Example

```rst
Configuration Selector Demo
===========================

Select your configuration:

.. config-selector::
   :options: os=Linux|Windows,version=22.04|24.04

Installation Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^

.. config-content::
   :show-when: os=Linux,version=22.04

   **Linux 22.04 Installation**
   
   .. code-block:: bash
   
       sudo apt update
       sudo apt install package-name

.. config-content::
   :show-when: os=Windows

   **Windows Installation**
   
   .. code-block:: bash
   
       # Use WSL2
       wsl --install
```

### Complex Example

```rst
.. config-selector::
   :options: platform=Ubuntu 22.04|Ubuntu 24.04|Windows,ros_distro=Humble|Jazzy,package_type=Default|Custom

.. config-content::
   :show-when: platform=Ubuntu 22.04,ros_distro=Humble,package_type=Default

   **Ubuntu 22.04 + Humble + Default Configuration**
   
   Specific instructions for this exact combination.

.. config-content::
   :show-when: platform=Windows

   **Windows Configuration**
   
   This appears for Windows regardless of other selections.
```

## Technical Details

### Components

1. **ConfigSelectorDirective**: 
   - Parses configuration options
   - Renders HTML selector widget
   - Injects CSS and JavaScript

2. **ConfigContentDirective**:
   - Wraps conditional content
   - Stores show-when conditions as data attributes

## Customization

### Styling

Override CSS classes to customize appearance:

```css
.config-selector {
    /* Customize selector appearance */
}

.config-options {
    /* Customize grid layout */
}

.config-select {
    /* Customize dropdown styling */
}
```

## Troubleshooting

### Content Not Showing/Hiding

- Check that show-when conditions exactly match selector values
- Ensure JavaScript is enabled
- Verify no syntax errors in configuration strings
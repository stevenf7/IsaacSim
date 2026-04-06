import json

from docutils import nodes
from docutils.parsers.rst import Directive, directives


class config_selector(nodes.General, nodes.Element):
    """Node for the configuration selector widget"""

    pass


class config_content(nodes.General, nodes.Element):
    """Node for content that should be shown/hidden based on configuration"""

    pass


class ConfigSelectorDirective(Directive):
    """
    Directive to create a configuration selector at the top of the page.

    Usage:
    .. config-selector::
       :options: platform=Ubuntu 22.04|Ubuntu 24.04|Windows,ros_distro=Humble|Jazzy,package_type=Default|Custom
       :dependencies: install_method=platform:Windows

    The optional ``:dependencies:`` option accepts a comma-separated list of
    ``key=dep_key:dep_value`` pairs.  A row tagged this way is only visible
    when the named dependency key has the specified value.
    """

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "options": directives.unchanged_required,
        "dependencies": directives.unchanged,
    }

    def run(self):
        # Parse the options string
        options_str = self.options.get("options", "")
        deps_str = self.options.get("dependencies", "")
        config_options = {}
        config_deps = {}

        for option_pair in options_str.split(","):
            if "=" in option_pair:
                key, values = option_pair.strip().split("=", 1)
                config_options[key.strip()] = [v.strip() for v in values.split("|")]

        # Parse dependencies: "install_method=platform:Windows" means the
        # install_method row is only shown when platform == Windows.
        for dep_pair in deps_str.split(",") if deps_str else []:
            dep_pair = dep_pair.strip()
            if "=" in dep_pair:
                key, dep = dep_pair.split("=", 1)
                if ":" in dep:
                    dep_key, dep_value = dep.split(":", 1)
                    config_deps[key.strip()] = {dep_key.strip(): dep_value.strip()}

        return [config_selector(config_options=config_options, config_deps=config_deps)]


class ConfigContentDirective(Directive):
    """
    Directive to wrap content that should be shown/hidden based on configuration.

    Usage:
    .. config-content::
       :show-when: platform=Ubuntu 22.04,ros_distro=Humble

       Content that only shows when Ubuntu 22.04 and Humble are selected.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "show-when": directives.unchanged_required,
    }

    def run(self):
        # Parse the show-when conditions
        show_when_str = self.options.get("show-when", "")
        conditions = {}

        for condition in show_when_str.split(","):
            if "=" in condition:
                key, value = condition.strip().split("=", 1)
                conditions[key.strip()] = value.strip()

        # Create the content node
        content_node = config_content(conditions=conditions)

        # Parse the content
        self.state.nested_parse(self.content, self.content_offset, content_node)

        return [content_node]


def visit_config_selector_html(self, node):
    """Render the configuration selector as HTML"""
    config_options = node.get("config_options", {})
    config_deps = node.get("config_deps", {})

    # Generate unique IDs for the selectors
    selector_html = ['<div class="config-selector" id="config-selector">']
    selector_html.append("<h3>Configuration</h3>")
    selector_html.append('<div class="config-options">')

    for key, values in config_options.items():
        dep = config_deps.get(key)
        if dep:
            dep_json = json.dumps(dep).replace('"', "&quot;")
            selector_html.append(f'<div class="config-row" data-show-when="{dep_json}">')
        else:
            selector_html.append(f'<div class="config-row">')
        selector_html.append(f'<div class="config-label">{key.replace("_", " ").title()}:</div>')
        selector_html.append(f'<div class="config-buttons" data-config-key="{key}">')

        for i, value in enumerate(values):
            active_class = "active" if i == 0 else ""
            clean_value = value.replace(" ", "_").replace(".", "_")
            selector_html.append(
                f'<button class="config-btn {active_class}" data-value="{value}" data-key="{key}" id="{key}_{clean_value}">{value}</button>'
            )

        selector_html.append("</div>")
        selector_html.append("</div>")

    selector_html.append("</div>")
    selector_html.append("</div>")

    # Add CSS and JavaScript
    css = """
    <style>
    .config-selector {
        background-color: var(--pst-color-surface, var(--color-background-secondary, #f8f9fa));
        border: 1px solid var(--pst-color-border, var(--color-border, #dee2e6));
        border-radius: 6px;
        padding: 16px;
        margin: 16px 0;
        box-shadow: 0 2px 8px var(--pst-color-shadow, rgba(0,0,0,0.1));
    }
    
    [data-theme="dark"] .config-selector {
        background-color: var(--pst-color-surface, #1e1e1e);
        border-color: var(--pst-color-border, #404040);
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    
    .config-selector h3 {
        margin-top: 0;
        margin-bottom: 12px;
        color: var(--pst-color-text-base, var(--color-foreground-primary, #212529));
        font-size: 1.1em;
        font-weight: 600;
    }
    
    [data-theme="dark"] .config-selector h3 {
        color: var(--pst-color-text-base, #ffffff);
    }
    
    .config-options {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    
    .config-row {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .config-label {
        font-weight: 600;
        color: var(--pst-color-text-base, var(--color-foreground-primary, #212529));
        font-size: 14px;
        margin-bottom: 2px;
    }
    
    [data-theme="dark"] .config-label {
        color: var(--pst-color-text-base, #ffffff);
    }
    
    .config-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    
    .config-btn {
        padding: 8px 12px;
        border: 2px solid var(--pst-color-border, var(--color-border, #dee2e6));
        border-radius: 6px;
        background-color: var(--pst-color-surface, var(--color-background-primary, #ffffff));
        color: var(--pst-color-text-base, var(--color-foreground-primary, #212529));
        font-size: 13px;
        font-weight: 500;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        white-space: nowrap;
        user-select: none;
        outline: none;
    }
    
    [data-theme="dark"] .config-btn {
        border-color: var(--pst-color-border, #404040);
        background-color: var(--pst-color-surface, #2d2d2d);
        color: var(--pst-color-text-base, #cccccc);
    }
    
    .config-btn:hover {
        border-color: var(--pst-color-primary, var(--color-brand-primary, #0d6efd));
        background-color: var(--pst-color-primary-bg, var(--color-background-hover, #e9ecef));
        color: var(--pst-color-text-base, var(--color-foreground-primary, #212529));
    }
    
    [data-theme="dark"] .config-btn:hover {
        border-color: #666666;
        background-color: #3d3d3d;
        color: #ffffff;
    }
    
    .config-btn.active {
        border-color: #76b900;
        background-color: #76b900;
        color: #ffffff;
        font-weight: 600;
    }
    
    .config-btn.active:hover {
        border-color: #669900;
        background-color: #669900;
        color: #ffffff;
    }
    
    .config-btn:focus {
        box-shadow: 0 0 0 3px rgba(118, 185, 0, 0.2);
    }
    
    .config-content {
        transition: opacity 0.3s ease-in-out;
    }
    
    .config-content.hidden {
        display: none;
    }
    
    @media (max-width: 768px) {
        .config-selector {
            padding: 12px;
            margin: 12px 0;
        }
        
        .config-options {
            gap: 14px;
        }
        
        .config-row {
            gap: 6px;
        }
        
        .config-label {
            font-size: 13px;
        }
        
        .config-btn {
            padding: 6px 10px;
            font-size: 12px;
        }
    }
    </style>
    """

    js = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const buttons = document.querySelectorAll('.config-btn');
        const contents = document.querySelectorAll('.config-content');

        // Returns the active value for each visible config row.
        // Rows hidden by a data-show-when dependency are excluded so their
        // value does not accidentally filter out content blocks.
        function getCurrentConfig() {
            const config = {};
            const buttonGroups = document.querySelectorAll('.config-buttons');

            buttonGroups.forEach(group => {
                const row = group.closest('.config-row');
                if (row && row.style.display === 'none') return;

                const activeBtn = group.querySelector('.config-btn.active');
                if (activeBtn) {
                    config[group.dataset.configKey] = activeBtn.dataset.value;
                }
            });

            return config;
        }

        // Show or hide config rows that have a data-show-when dependency.
        // Must be called before updateVisibility() so getCurrentConfig() is correct.
        function updateRowVisibility() {
            const config = getCurrentConfig();
            document.querySelectorAll('.config-row[data-show-when]').forEach(row => {
                try {
                    const showWhen = JSON.parse(row.dataset.showWhen || '{}');
                    const visible = Object.entries(showWhen).every(([k, v]) => config[k] === v);
                    row.style.display = visible ? '' : 'none';
                } catch (e) {
                    console.warn('Error parsing data-show-when for row:', e);
                }
            });
        }

        function updateVisibility() {
            const currentConfig = getCurrentConfig();

            contents.forEach(content => {
                try {
                    const conditions = JSON.parse(content.dataset.conditions || '{}');
                    const shouldShow = Object.entries(conditions).every(
                        ([key, value]) => currentConfig[key] === value
                    );

                    if (shouldShow) {
                        content.classList.remove('hidden');
                        content.style.display = 'block';
                    } else {
                        content.classList.add('hidden');
                        content.style.display = 'none';
                    }
                } catch (e) {
                    console.warn('Error parsing conditions for content block:', e);
                }
            });
        }

        // Add click event listeners to buttons
        buttons.forEach(button => {
            button.addEventListener('click', function() {
                this.parentNode.querySelectorAll('.config-btn').forEach(s => s.classList.remove('active'));
                this.classList.add('active');

                // Row visibility must be updated before content visibility.
                updateRowVisibility();
                updateVisibility();
            });

            button.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.click();
                }
            });
        });

        // Initial update
        setTimeout(function() {
            updateRowVisibility();
            updateVisibility();
        }, 100);

        // Watch for theme changes
    });
    </script>
    """

    self.body.append(css)
    self.body.append("".join(selector_html))
    self.body.append(js)


def depart_config_selector_html(self, node):
    pass


def visit_config_content_html(self, node):
    """Render the config content wrapper"""
    conditions = node.get("conditions", {})
    conditions_json = json.dumps(conditions).replace('"', "&quot;")

    self.body.append(f'<div class="config-content" data-conditions="{conditions_json}">')


def depart_config_content_html(self, node):
    self.body.append("</div>")


def setup(app):
    """Setup the extension"""
    app.add_node(config_selector, html=(visit_config_selector_html, depart_config_selector_html))
    app.add_node(config_content, html=(visit_config_content_html, depart_config_content_html))
    app.add_directive("config-selector", ConfigSelectorDirective)
    app.add_directive("config-content", ConfigContentDirective)

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

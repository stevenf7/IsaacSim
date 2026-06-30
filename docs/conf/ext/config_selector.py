from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping, MutableMapping
from html import escape
from typing import ClassVar, TypedDict, cast

from docutils import nodes  # type: ignore[import-untyped]
from docutils.parsers.rst import Directive, directives  # type: ignore[import-untyped]
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.writers.html5 import HTML5Translator

ConfigConditions = dict[str, str]
ConfigDependencies = dict[str, ConfigConditions]
ConfigOptions = dict[str, list[str]]
DirectiveOption = Callable[[str], str]

_CONFIG_SELECTOR_STATIC_PATH = "design_static"
_CONFIG_SELECTOR_JS = "isaacsim-config-selector.js"
_CONFIG_SELECTOR_SCOPES_KEY = "config_selector_scopes"


class ExtensionMetadata(TypedDict):
    """Metadata returned to Sphinx when the extension is registered."""

    version: str
    parallel_read_safe: bool
    parallel_write_safe: bool


class config_selector(nodes.General, nodes.Element):  # type: ignore[misc]
    """Node for the configuration selector widget."""

    pass


class config_content(nodes.General, nodes.Element):  # type: ignore[misc]
    """Node for content that should be shown/hidden based on configuration."""

    pass


def _option_str(options: Mapping[str, str], key: str, default: str) -> str:
    return options.get(key, default)


def _normalize_scope(scope: str) -> str:
    normalized_scope = re.sub(r"[^A-Za-z0-9_-]+", "-", scope.strip()).strip("-")
    return normalized_scope or "default"


def _normalize_id_part(identifier: str, fallback: str) -> str:
    normalized_identifier = re.sub(r"[^A-Za-z0-9_-]+", "-", identifier.strip()).strip("-")
    return normalized_identifier or fallback


def _persist_mode(argument: str) -> str:
    mode = argument.strip().lower()
    if mode != "session":
        raise ValueError(':persist: must be "session"')
    return mode


def _document_temp_data(document: nodes.document) -> MutableMapping[str, str] | None:
    settings = getattr(document, "settings", None)
    env = getattr(settings, "env", None)
    temp_data = getattr(env, "temp_data", None)
    if isinstance(temp_data, MutableMapping):
        return cast(MutableMapping[str, str], temp_data)
    return None


def _current_selector_scope(document: nodes.document) -> str:
    temp_data = _document_temp_data(document)
    if temp_data is None:
        return "default"

    scope = temp_data.get("config_selector_scope", "default")
    if isinstance(scope, str):
        return scope
    return "default"


def _set_current_selector_scope(document: nodes.document, scope: str) -> None:
    temp_data = _document_temp_data(document)
    if temp_data is not None:
        temp_data["config_selector_scope"] = scope


def _register_selector_scope(document: nodes.document, scope: str, line: int) -> None:
    temp_data = _document_temp_data(document)
    if temp_data is None:
        return

    used_scopes = temp_data.get(_CONFIG_SELECTOR_SCOPES_KEY, "")
    used_scope_list = used_scopes.split(",") if used_scopes else []
    if scope in used_scope_list:
        document.reporter.warning(
            f'config-selector scope "{scope}" is used more than once in this document; '
            "set a unique :scope: to avoid duplicate HTML IDs and shared URL parameters.",
            line=line,
        )
        return

    used_scope_list.append(scope)
    temp_data[_CONFIG_SELECTOR_SCOPES_KEY] = ",".join(used_scope_list)


def _parse_config_options(options_str: str) -> ConfigOptions:
    config_options: ConfigOptions = {}

    for option_pair in options_str.split(","):
        if "=" in option_pair:
            key, values = option_pair.strip().split("=", 1)
            config_options[key.strip()] = [value.strip() for value in values.split("|")]

    return config_options


def _parse_dependencies(deps_str: str) -> ConfigDependencies:
    config_deps: ConfigDependencies = {}

    for dep_pair in deps_str.split(",") if deps_str else []:
        dep_pair = dep_pair.strip()
        if "=" not in dep_pair:
            continue

        key, dep = dep_pair.split("=", 1)
        conditions: ConfigConditions = {}
        for dep_condition in dep.split(";"):
            if ":" in dep_condition:
                dep_key, dep_value = dep_condition.split(":", 1)
                conditions[dep_key.strip()] = dep_value.strip()
        if conditions:
            config_deps[key.strip()] = conditions

    return config_deps


def _parse_conditions(show_when_str: str) -> ConfigConditions:
    conditions: ConfigConditions = {}

    for condition in show_when_str.split(","):
        if "=" in condition:
            key, value = condition.strip().split("=", 1)
            conditions[key.strip()] = value.strip()

    return conditions


def _node_str(node: config_selector | config_content, key: str, default: str) -> str:
    return cast(str, node.get(key, default))


def _node_config_options(node: config_selector) -> ConfigOptions:
    return cast(ConfigOptions, node.get("config_options", {}))


def _node_config_deps(node: config_selector) -> ConfigDependencies:
    return cast(ConfigDependencies, node.get("config_deps", {}))


def _node_conditions(node: config_content) -> ConfigConditions:
    return cast(ConfigConditions, node.get("conditions", {}))


class ConfigSelectorDirective(Directive):  # type: ignore[misc]
    """
    Directive to create a configuration selector at the top of the page.

    Usage:
    .. config-selector::
       :scope: setup
       :options: platform=Linux|Windows,mode=Standard|Advanced
       :dependencies: mode=platform:Linux

    The optional ``:dependencies:`` option accepts a comma-separated list of
    ``key=dep_key:dep_value`` pairs. A row tagged this way is only visible
    when the named dependency key has the specified value. Multiple conditions
    for the same row can be separated by semicolons, for example
    ``mode=platform:Linux;edition:Advanced``.
    """

    has_content: ClassVar[bool] = False
    required_arguments: ClassVar[int] = 0
    optional_arguments: ClassVar[int] = 0
    option_spec: ClassVar[dict[str, DirectiveOption]] = {
        "options": directives.unchanged_required,
        "dependencies": directives.unchanged,
        "title": directives.unchanged,
        "scope": directives.unchanged,
        "persist": _persist_mode,
        "persist-key": directives.unchanged,
    }

    def run(self) -> list[config_selector]:
        options = cast(Mapping[str, str], self.options)
        options_str = _option_str(options, "options", "")
        deps_str = _option_str(options, "dependencies", "")
        title = _option_str(options, "title", "Configuration").strip()
        scope = _normalize_scope(_option_str(options, "scope", "default"))
        persist = _option_str(options, "persist", "")
        persist_key = _normalize_id_part(_option_str(options, "persist-key", scope), scope)
        _register_selector_scope(self.state.document, scope, self.lineno)
        _set_current_selector_scope(self.state.document, scope)

        # Parse dependencies: "mode=platform:Linux" means the
        # mode row is only shown when platform == Linux. Multiple
        # dependency conditions for one row can be separated with semicolons.
        selector_node = config_selector(
            config_options=_parse_config_options(options_str),
            config_deps=_parse_dependencies(deps_str),
            title=title,
            scope=scope,
            persist=persist,
            persist_key=persist_key,
        )
        return [selector_node]


class ConfigContentDirective(Directive):  # type: ignore[misc]
    """
    Directive to wrap content that should be shown/hidden based on configuration.

    Usage:
    .. config-content::
       :show-when: platform=Linux,mode=Advanced

       Content that only shows when Linux and Advanced are selected.
    """

    has_content: ClassVar[bool] = True
    required_arguments: ClassVar[int] = 0
    optional_arguments: ClassVar[int] = 0
    option_spec: ClassVar[dict[str, DirectiveOption]] = {
        "show-when": directives.unchanged_required,
        "scope": directives.unchanged,
    }

    def run(self) -> list[config_content]:
        options = cast(Mapping[str, str], self.options)
        show_when_str = _option_str(options, "show-when", "")
        scope = _normalize_scope(_option_str(options, "scope", _current_selector_scope(self.state.document)))
        content_node = config_content(conditions=_parse_conditions(show_when_str), scope=scope)

        self.state.nested_parse(self.content, self.content_offset, content_node)
        return [content_node]


def visit_config_selector_html(translator: HTML5Translator, node: config_selector) -> None:
    """Render the configuration selector as HTML."""

    config_options = _node_config_options(node)
    config_deps = _node_config_deps(node)
    title = _node_str(node, "title", "Configuration")
    scope = _node_str(node, "scope", "default")
    persist = _node_str(node, "persist", "")
    persist_key = _node_str(node, "persist_key", scope)
    selector_id = f"config-selector-{scope}"
    scope_attr = escape(scope, quote=True)
    title_attr = escape(title, quote=True)
    title_text = escape(title, quote=False)

    selector_html = [
        f'<div class="config-selector" id="{escape(selector_id, quote=True)}" data-config-scope="{scope_attr}" role="region" aria-label="{title_attr} selector">'
    ]
    selector_html.append(f"<h3>{title_text}</h3>")
    selector_html.append('<div class="config-options">')

    for key, values in config_options.items():
        dep = config_deps.get(key)
        if dep:
            dep_json = escape(json.dumps(dep, separators=(",", ":")), quote=True)
            selector_html.append(f'<div class="config-row" data-show-when="{dep_json}">')
        else:
            selector_html.append('<div class="config-row">')
        key_label = escape(key.replace("_", " ").title(), quote=False)
        key_attr = escape(key, quote=True)
        selector_html.append(f'<div class="config-label">{key_label}:</div>')
        selector_html.append(f'<div class="config-buttons" data-config-key="{key_attr}">')

        for i, value in enumerate(values):
            active_class = "active" if i == 0 else ""
            pressed = "true" if i == 0 else "false"
            key_id = _normalize_id_part(key, "key")
            value_id = _normalize_id_part(value, "value")
            button_id = f"{scope}_{key_id}_{i}_{value_id}"
            value_attr = escape(value, quote=True)
            value_text = escape(value, quote=False)
            selector_html.append(
                f'<button type="button" class="config-btn btn btn-sm btn-outline-primary {active_class}" data-value="{value_attr}" data-key="{key_attr}" id="{button_id}" aria-pressed="{pressed}">{value_text}</button>'
            )

        selector_html.append("</div>")
        selector_html.append("</div>")

    selector_html.append("</div>")

    metadata_json = json.dumps(
        {
            "scope": scope,
            "title": title,
            "options": config_options,
            "dependencies": config_deps,
            "persist": persist,
            "persistKey": persist_key,
        },
        separators=(",", ":"),
    ).replace("</", "<\\/")
    selector_html.append(
        f'<script type="application/json" class="config-selector-metadata" data-config-scope="{scope_attr}">{metadata_json}</script>'
    )
    selector_html.append("</div>")

    translator.body.append("".join(selector_html))


def depart_config_selector_html(_translator: HTML5Translator, _node: config_selector) -> None:
    pass


def visit_config_content_html(translator: HTML5Translator, node: config_content) -> None:
    """Render the config content wrapper."""

    conditions = _node_conditions(node)
    scope = _node_str(node, "scope", "default")
    conditions_json = escape(json.dumps(conditions, separators=(",", ":")), quote=True)

    translator.body.append(
        f'<div class="config-content" data-config-scope="{escape(scope, quote=True)}" data-conditions="{conditions_json}">'
    )


def depart_config_content_html(translator: HTML5Translator, _node: config_content) -> None:
    translator.body.append("</div>")


def _on_config_inited(_app: Sphinx, config: Config) -> None:
    if _CONFIG_SELECTOR_STATIC_PATH not in config.html_static_path:
        config.html_static_path.append(_CONFIG_SELECTOR_STATIC_PATH)


def setup(app: Sphinx) -> ExtensionMetadata:
    """Set up the extension."""

    app.add_node(config_selector, html=(visit_config_selector_html, depart_config_selector_html))
    app.add_node(config_content, html=(visit_config_content_html, depart_config_content_html))
    app.add_directive("config-selector", ConfigSelectorDirective)
    app.add_directive("config-content", ConfigContentDirective)
    app.add_js_file(_CONFIG_SELECTOR_JS)
    app.connect("config-inited", _on_config_inited)

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

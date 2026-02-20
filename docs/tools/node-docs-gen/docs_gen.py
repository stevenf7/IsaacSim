import argparse
import json
import os
import re
import shutil

import yaml
from gitlab import change_branch, commit_and_push_branch, create_branch
from jinja2 import Environment, FileSystemLoader
from yaml.loader import SafeLoader

JINJA_ENV = Environment(loader=FileSystemLoader("templates/"))
CUSTOM_CONTENT_TEMPLATES = {
    "pre": os.path.join("custom", "{extension}-{node}-pre.rst"),
    "post": os.path.join("custom", "{extension}-{node}-post.rst"),
}


def _custom_data(dir_, extension, node):
    pre_custom_content_path = os.path.join(
        dir_, "nodes", CUSTOM_CONTENT_TEMPLATES["pre"].format(extension=extension, node=node)
    )
    pre_exists = os.path.isfile(pre_custom_content_path)

    post_custom_content_path = os.path.join(
        dir_, "nodes", CUSTOM_CONTENT_TEMPLATES["post"].format(extension=extension, node=node)
    )
    post_exists = os.path.isfile(post_custom_content_path)

    return ((pre_exists and f"{node}-pre.rst"), (post_exists and f"{node}-post.rst"))


def _path_from_root(path):
    components = path.split(os.sep)
    components.reverse()
    path = []
    for component in components:
        if component == "docs":
            return os.path.join(*path)
        else:
            path.insert(0, component)
    return os.path.join(*path)


def _ogn_data(filepath):
    with open(filepath, "r") as f:
        data = json.load(f)
        return list(data.items())[0]


def _parse_name(name, obj):
    try:
        if obj.get("uiName"):
            name = f'{obj["uiName"]} ({name})'
    except AttributeError:
        print(f"There is no uiName for {obj}")
    return name


def _parse_description(obj):
    if isinstance(obj, str):
        description = obj
    else:
        description = obj.get("description", "")
        if not isinstance(description, str):
            description = " ".join(description)
    return description.replace('"', "").replace("*", "'*'").replace("\n", " ")


def _parse_type(obj):
    type_ = obj.get("type", "")

    if type_ == "":
        return type_

    if isinstance(type_, str):
        type_ = "``" + type_.replace('"', "") + "``"
    else:
        type_ = ", ".join(["``" + t.replace('"', "") + "``" for t in type_])
    return type_


def _build_table(items):
    constraints = []
    contents = []
    for k, v in items:
        if k == "$constraint":
            constraints.append(v)
            continue
        if k == "$comment":
            continue
        name = _parse_name(k, v)
        description = _parse_description(v)
        type_ = _parse_type(v)
        default = str(v.get("default", ""))
        contents.append(",".join([f'"{name}"', f'"{type_}"', f'"{description}"', f'"{default}"']))
    return "\n   ".join(contents), constraints


def _parse_category(ogn_data):
    try:
        categories = ogn_data.get("categories", ["common"])
    except AttributeError:
        category = "common"
    else:
        if isinstance(categories, list):
            if len(categories) >= 1:
                category = categories[0]
            else:
                category = "common"
        elif isinstance(categories, str):
            category = categories
        else:
            category = "common"

    category = category.lower()
    category = category.replace(":", "-")
    category = category.replace(".", "-")
    category = category.replace("_", "-")
    category = category.replace(" ", "-")
    return category


def _parse_extension(ogn_file):
    pattern = "extensions\/(.+?)\/"
    match = re.search(pattern, ogn_file)
    if match:
        return match.group(1)
    return None


def _gen_node(dir_, node):
    template = JINJA_ENV.get_template("node-doc.rst")

    # get default title (extension path)
    ogn_title, ogn_data = _ogn_data(node["ogn_file"])
    filename = f'{ogn_title.replace(".", "-").lower()}-{ogn_data.get("version", 1)}'

    # metadata uiName is preferred over ext path
    if ogn_data.get("metadata", {}).get("uiName", ""):
        ogn_title = ogn_data["metadata"]["uiName"]
        pass
        # print("GOT METADATA NAME: " + ogn_title, flush=True)

    # preferred name over all
    if "uiName" in ogn_data:
        ogn_title = f"{ogn_data['uiName']}"

    # filter out "hidden" nodes
    if ogn_data.get("metadata", {}).get("hidden", False):
        return "hidden node", None, None

    description = _parse_description(ogn_data)
    category = _parse_category(ogn_data)
    node_extension = _parse_extension(node["ogn_file"])

    kwargs = {
        "title": ogn_title,
        "image": node.get("image"),
        "description": description,
        "keywords": " ".join(node["keywords"]),
        "node_extension": node_extension,
    }

    try:
        kwargs["inputs"], kwargs["input_constraints"] = _build_table(ogn_data["inputs"].items())
    except KeyError:
        pass
    except TypeError:
        kwargs["inputs"], kwargs["input_constraints"] = "", []

    try:
        kwargs["outputs"], kwargs["output_constraints"] = _build_table(ogn_data["outputs"].items())
    except KeyError:
        pass
    except TypeError:
        kwargs["outputs"], kwargs["output_constraints"] = "", []

    node_extension = node_extension.replace(".", "-").lower()
    custom_data_pre, custom_data_post = _custom_data(dir_, node_extension, filename)
    if custom_data_pre:
        kwargs["custom_content_pre"] = os.path.join(
            "/prod_extensions/ext_omnigraph/node-library/nodes",
            CUSTOM_CONTENT_TEMPLATES["pre"].format(extension=node_extension, node=filename),
        ).replace("\\", "/")
    if custom_data_post:
        kwargs["custom_content_post"] = os.path.join(
            "/prod_extensions/ext_omnigraph/node-library/nodes",
            CUSTOM_CONTENT_TEMPLATES["post"].format(extension=node_extension, node=filename),
        ).replace("\\", "/")

    extension_path = os.path.join(dir_, "nodes", node_extension)
    try:
        os.mkdir(extension_path)
    except FileExistsError:
        pass

    node_path = os.path.join(extension_path, f"{filename}.rst")
    with open(node_path, "w") as f:
        f.write(template.render(**kwargs))

    return category, ogn_title, f"nodes/{node_extension}/{filename}.rst"


def format_category_name(category):
    name = " ".join(category.split("-")).title()
    return f"{name} Nodes"


def _build_library(root_dir, category_nodes):
    library_path = os.path.join(root_dir, f"node-library.rst")

    if not os.path.exists(library_path):
        template = JINJA_ENV.get_template("node-library.rst")
        with open(library_path, "w") as f:
            category_order = list(category_nodes.keys())
            category_order.sort()
            kwargs = {
                "category_nodes": category_nodes,
                "category_order": category_order,
            }
            f.write(template.render(**kwargs))
    else:
        print(f"Library already exists at {library_path}")


def generate(dir_, skip_categories):
    config_path = os.path.join(dir_, "node_lib_config.yaml")
    with open(config_path) as f:
        try:
            nodes = yaml.load(f, Loader=SafeLoader)["nodes"]
            category_nodes = {}
            for node in nodes:
                category, ogn_title, node_doc_path = _gen_node(dir_, node)
                if category:
                    if not category == "hidden node":
                        if category.lower() not in skip_categories:
                            category_name = format_category_name(category)
                            if category_name in category_nodes:
                                category_nodes[category_name].append((ogn_title, node_doc_path))
                            else:
                                category_nodes[category_name] = [(ogn_title, node_doc_path)]
                    else:
                        print(f"Skipped hidden node: {node['ogn_file']}", flush=True)
                else:
                    print(f"Missing Category: {node['ogn_file']}", flush=True)
            _build_library(dir_, category_nodes)
        except yaml.parser.ParserError as pe:
            print("Invalid yaml:\n\n", pe)
            return


def to_kebab_case(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", name)
    name = re.sub("__([A-Z])", r"-\1", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1-\2", name)
    name = name.lower()

    if name.startswith("ogn-"):
        name = name[4:]

    if name.endswith(".ogn"):
        name = name[:-4]

    return name


def _get_ogn_files(dir_):
    ogn_files = []
    for f in os.listdir(dir_):
        if f.endswith(".ogn"):
            name = to_kebab_case(f)
            path = os.path.join(dir_, f)
            ogn_files.append((name, path))
    return ogn_files


def dedupe_nodes(node_list):
    """Remove duplicate node descriptions from a Node list.

    This script clones every repository that contains OGN files.
    Some of those repositories are forks of other repositories and,
    therefore, contain duplicate OGN files. This function removes
    the duplicated definitions of OGN files.
    """
    cache = {}
    for node in node_list:
        ogn_title, ogn_data = _ogn_data(node["ogn_path"])
        # category = _parse_category(ogn_data)
        version = ogn_data.get("version", 1)
        extension = _parse_extension(node["ogn_path"])

        node_key = (ogn_title, version, extension)
        if node_key not in cache:
            cache[node_key] = node
        else:
            print(f"Deduping: ogn_title: {ogn_title}  version: {version}  extension: {extension}", flush=True)

    # just return the nodes (cache indices only for deduping)
    return cache.values()


# Setup output directories (staging area) using the node registry
def scaffold(dir_, source_dirs):
    nodes_path = os.path.join(dir_, "nodes")
    custom_content_path = os.path.join(nodes_path, "custom")
    node_lib_path = os.path.join(dir_, "node_lib_config.yaml")

    # nuke the output directory
    try:
        shutil.rmtree(dir_)
    except FileNotFoundError:
        pass

    # (re) create output dir
    try:
        os.mkdir(dir_)
    except FileExistsError:
        pass

    # create nodes dir in output dir
    try:
        os.mkdir(nodes_path)
    except FileExistsError:
        pass

    template = JINJA_ENV.get_template("node_template.yaml")

    # Copy the custom files create output directories
    shutil.copytree("custom", custom_content_path)

    # create
    ogn_files = []
    for source_dir in source_dirs:
        ogn_files += _get_ogn_files(source_dir)

    try:
        with open(node_lib_path, "x") as f:
            if ogn_files:
                nodes = [
                    {
                        "name": name,
                        "keyword": name,
                        "ogn_path": path,
                    }
                    for name, path in ogn_files
                ]
                print(f"Pre: dedupe_nodes")  # \n{nodes}")
                nodes = dedupe_nodes(nodes)
                # print(f"Post: dedupe_nodes...")

                f.write(template.render(nodes=nodes))
            else:
                f.write(
                    template.render(
                        nodes=[
                            {
                                "name": "<file name here (without extension)>",
                                "keyword": "<any keywords to help improve search>",
                                "ogn_path": "<path to OGN file on local machine>.ogn",
                            }
                        ]
                    )
                )
    except FileExistsError:
        print("Config file already exists!")


def copy_output_to_omni_docs(output_dir, branch, should_commit):
    repo_path = "../.."
    destination = f"{repo_path}/docs/prod_extensions/ext_omnigraph/node-library"
    shutil.rmtree(destination)
    shutil.copytree(output_dir, destination)

    if should_commit:
        create_branch(repo_path, branch)
        commit_and_push_branch(repo_path, branch)
        change_branch(repo_path, "-")


def _clean_directory(dir_):
    path = _path_from_root(dir_)
    path = os.path.normpath(path)
    return path


def generate_for_directories(directories, skip_categories, branch, should_commit):
    root_output_directory = "output"

    # create output directories using the node registry
    scaffold(root_output_directory, directories)

    generate(root_output_directory, skip_categories)
    copy_output_to_omni_docs(root_output_directory, branch, should_commit)

import argparse
from datetime import date

import yaml
from docs_gen import generate_for_directories
from gitlab import clone_repository, get_project_data, search_gitlab
from local import (
    read_node_registry,
    read_paths_json,
    read_projects_json,
    write_paths_json,
    write_projects_json,
    write_registry,
)

# Hardcoded in the gitlab API
PAGE_SIZE = 20


def merge_project_data(existing_projects, incoming_projects):
    for project_id, paths in incoming_projects.items():
        existing_projects[project_id] = existing_projects.get(project_id, []) + paths
    return existing_projects


def pull_from_gitlab(skip_projects):
    aggregate_results = {}
    running = True
    page = 1

    while running:
        print(f"Getting page {page}", flush=True)
        search_results, num_results = search_gitlab(page, skip_projects)
        aggregate_results = merge_project_data(aggregate_results, search_results)

        # If the last page had 20 then it will still return
        # another page with zero size
        is_last_page = num_results < PAGE_SIZE
        if is_last_page:
            running = False
        else:
            page += 1

    return aggregate_results


def format_node_registry():
    # create paths for all nodes by appending the
    # extensions' nodes path(s) to their repo's path

    # "data/search_results.json" list of ext's for each repo id
    projects = read_projects_json()

    # "data/paths.json" contains the local path
    # for each repo/project id
    repo_paths = read_paths_json()

    ogn_registry = []
    for id_, repo_path in repo_paths.items():
        og_paths = projects[id_]
        for path_suffix in og_paths:
            full_path = f"{repo_path}/{path_suffix}"

            # strip off .ogn file name from path
            stripped_path = "/".join(full_path.split("/")[0:-1])

            # add if unique (several .ogn's can share a given directory)
            if not stripped_path in ogn_registry:
                ogn_registry.append(stripped_path)

    # "data/ogn_registry.json" will contain paths for all nodes
    write_registry(ogn_registry)
    return ogn_registry


def parse_config():
    with open("skip_projects.yaml", "r") as conf:
        conf = yaml.safe_load(conf)
        skip_projects = conf["skip_projects"]
        skip_projects = {project["id"]: project["extensions"] for project in skip_projects}

        skip_categories = [c.lower() for c in conf["skip_categories"]]
    return skip_projects, skip_categories


if __name__ == "__main__":
    today = date.today()

    parser = argparse.ArgumentParser(description="Generate OmniGraph node documentation.")
    parser.add_argument(
        "--stage",
        help="Determines the stage at which the generator begins.",
        choices=["all", "clone", "generate"],
        default="all",
    )
    parser.add_argument(
        "--branch",
        help="Manually sets the output branch.",
        default=f"node-doc-gen-{today.day}.{today.month}.{today.year}",
    )
    parser.add_argument(
        "--commit",
        help="Uses git to commit changes and push an MR to GitLab.",
        action=argparse.BooleanOptionalAction,
    )
    args = parser.parse_args()

    # get projects and categories to skip from "config.yaml"
    skip_projects, skip_categories = parse_config()

    # "data/search_results.json" will contain a dictionary of
    # lists of extensions that passed the skip_projects filtering
    # indexed by repo id
    if args.stage == "all":
        projects = pull_from_gitlab(skip_projects)
        write_projects_json(projects)

    # clone/pull all projects/repos by ID
    if args.stage in ["all", "clone"]:
        projects = read_projects_json()
        project_paths = {}
        for project_id, paths in projects.items():
            url, path = get_project_data(project_id)
            local_path = clone_repository(url, path)
            if local_path:
                project_paths[project_id] = local_path
            else:
                print(f"Not indexing repo: {project_id}")

        # "data/paths.json" contains the local path
        # for each repo/project id
        write_paths_json(project_paths)

    if args.stage in ["all", "clone", "generate"]:
        # create list of paths for all nodes (several nodes may share a path)
        source_directories = format_node_registry()

        generate_for_directories(source_directories, skip_categories, args.branch, args.commit)

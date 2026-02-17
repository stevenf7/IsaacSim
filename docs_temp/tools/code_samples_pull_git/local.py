import json
import os


def _ensure_data_dir():
    try:
        os.mkdir("data")
    except FileExistsError:
        pass


def read_projects_json():
    _ensure_data_dir()
    with open("data/search_results.json", "r") as f:
        return json.load(f)


def read_paths_json():
    _ensure_data_dir()
    with open("data/paths.json", "r") as f:
        results = json.load(f)
        return results


def write_paths_json(results):
    _ensure_data_dir()
    with open("data/paths.json", "w+") as f:
        json.dump(results, f, indent=4)


def write_projects_json(results):
    _ensure_data_dir()
    with open("data/search_results.json", "w+") as f:
        json.dump(results, f, indent=4)


def write_registry(registry):
    _ensure_data_dir()
    with open("data/ogn_registry.json", "w+") as f:
        json.dump(registry, f, indent=4)


def read_node_registry():
    _ensure_data_dir()
    with open("data/ogn_registry.json", "r") as f:
        return json.load(f)

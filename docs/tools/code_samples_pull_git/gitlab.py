import os
import re

import requests
from git import Repo

API_PREFIX = f"https://gitlab-master.nvidia.com/api/v4"
HEADERS = {
    "PRIVATE-TOKEN": os.environ["PRIVATE_TOKEN"],
}
GROUP = 2393
SCOPE = "blobs"
QUERY = "extension:ogn"


# search for OGN files in all repos/projects in gitlab server
# into serialized json format
def search_gitlab(page, skip_projects):
    response = requests.get(
        f"{API_PREFIX}/groups/{GROUP}/search?scope={SCOPE}&page={page}&search={QUERY}", headers=HEADERS
    ).json()
    num_results = len(response)

    # filter out skip projects
    processed = _process_search_response(response, skip_projects)
    return processed, num_results


def _process_search_response(search_response, skip_projects):
    processed = {}
    for obj in search_response:
        project_id = str(obj["project_id"])
        path = obj["path"]

        # get list of extensions to skip with project_id from
        # config.yaml (could be empty list)
        extensions_to_skip = skip_projects.get(project_id, [])

        # if wildcard then skip entire project
        if extensions_to_skip and extensions_to_skip == "*":
            print(f"Skipping project {project_id}")
            continue
        elif extensions_to_skip:
            # check extensions in the list..
            # skip ogn if any extension names are in its path
            skip_pattern = rf"{'|'.join(extensions_to_skip)}"
            if re.search(skip_pattern, path):
                print(f"Skipping path {path} for project {project_id}")
                continue

        # passed filter so add it...
        if project_id in processed:
            processed[project_id].append(path)
        else:
            processed[project_id] = [path]
    return processed


# get repo meta data with project_id with auth key
def get_project_data(project_id):
    response = requests.get(f"{API_PREFIX}/projects/{project_id}", headers=HEADERS).json()

    return response["ssh_url_to_repo"], response["path"]


def create_branch(repo_path, branch_name):
    try:
        repo = Repo(repo_path)
        repo.git.checkout("-b", branch_name)
    except:
        print("Branch exists.")
        repo.git.checkout(branch_name)


def change_branch(repo_path, branch):
    repo = Repo(repo_path)
    repo.git.checkout(branch)


def commit_and_push_branch(repo_path, branch_name):
    repo = Repo(repo_path)
    print("Adding all files.")
    repo.git.add(all=True)
    print("Committing all files.")
    repo.index.commit("Regenerate OmniGraph node documentation")
    remote = repo.remote()
    print("Pushing branch.")
    remote.push(f"{branch_name}:{branch_name}", **{"push-option": "merge_request.create"})


def clone_repository(url, path):
    local_path = f"repos/{path}"
    print(f"Cloning repo: {url} : {path}", flush=True)
    if os.path.exists(local_path):
        print(f"Repository already exists at {local_path}; pulling latest changes")
        repo = Repo(local_path)
        origin = repo.remotes.origin
        try:
            origin.pull()
        except:
            print(f"Error Pulling Repo: {local_path}")
            # return False
    else:
        print(f"Cloning repository to {local_path}.")
        try:
            Repo.clone_from(url, local_path)
        except:
            print(f"Error Cloning Repo: {local_path}")
            # return False

    return local_path

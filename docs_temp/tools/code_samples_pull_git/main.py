# import argparse
# from datetime import date

import os

import requests

# import github
# import GitHub

# from github import GitHub
# from github import GithubException

# HEADERS = {
#     "PRIVATE-TOKEN": os.environ["PRIVATE_TOKEN"],
# }
MY_TOKEN = "---"

HEADERS = {
    "PRIVATE-TOKEN": MY_TOKEN,
}

headers = {"Authorization": "token " + MY_TOKEN}


def test_git_pull():

    # gith = github.GitHub(MY_TOKEN)

    # token = '1234'
    # headers = {'Authorization' : 'token ' + token }
    # data = {"event_type": "build"}
    # r = requests.get(test_url, headers=headers, data=data)

    # for k in r.headers:
    #     print(f"head: {k} : {r.headers[k]}")

    # for key in r.__dict__:
    #     print(key,r.__dict__[key])

    git_url = "https://github.com/NVIDIA-Omniverse/OpenUSD-Code-Samples.git"

    os.system(
        'GIT_SSH_COMMAND="ssh -i <insert your git private key here>" git clone ssh://git@github.com/<username>/<repo>.git'
    )

    from git import Repo

    Repo.clone_from(url, local_path)

    return

    local_pass_path = "pass.txt"

    repo_dest = os.path.curdir
    local_pass_path = repo_dest + "/" + local_pass_path
    print(f"local repo path: {local_pass_path}")
    if os.path.exists(local_pass_path):
        f = open(local_pass_path)
        print(f.read())

        from git import Repo

        # Repo.clone_from(git_url, repo_dir)

    return

    import sys

    print(sys.prefix)

    username = "KenBPayne"
    # old token is gone, using env vars now...

    # token = os.environ["GH-TOKEN"]
    # print(f"TOKEn = {token}")
    for k in os.environ:
        print(f"key: {k} : {os.environ[k]}")

    return

    login = requests.get(test_url, auth=(username, token)).content
    print(login)

    #    return

    # C:\OmniVerseDocs\Omni-docs-SSH\omni-docs\tools\code_samples_pull_git\main.py

    f = open("test_REQ.html", "wb")
    f.write(login)
    f.close()

    return

    for chunk in login.iter_content(chunk_size=512 * 1024):
        if chunk:
            f.write(chunk)
            print(chunk)
    f.close()

    # for key in login.__dict__:
    #     print(key,login.__dict__[key])

    # print(r.headers['Content-Type'])


# for hkey in r.headers:
#    print(f"HEADERS: {hkey} : {r.headers[hkey]}")
# cls
# print(r.__dict__)

# head_check = ["host",]
# for k in head_check:
#     print(f"head: {k} : {r.headers[k]}")


# print (r.text)


if __name__ == "__main__":

    test_git_pull()

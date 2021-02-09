# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


# Taken from https://gitlab-master.nvidia.com/omniverse/kit/-/blob/master/kit/source/extensions/omni.kit.registry.nucleus/omni/kit/registry/nucleus/slack_notifier.py

import json as _json
import http.client
import ssl

from typing import List

# Note: to write to a channel, you need to:
# 1. add the "kit-updates" app to the channel
# 2. configure the app to post to the channel, see https://nvidia.slack.com/apps/A0199V560FK-kit-updates?settings=1&next_id=0
# (you need to add an "incoming webhook")
SLACK_HOST = "slack.com"
SLACK_HOOK_HOST = "hooks.slack.com"
# this is tied to a specific channel, in this case #ct-omni-isaacsim-changelog
SLACK_HOOK_URL = "/services/T04SYRAP3/B01M48YHV4Z/sLuEg1fLu2qHhUbAbvML4Hfh"


def _post(host, url, json=None, headers=None):
    client = http.client.HTTPSConnection(host, context=ssl._create_unverified_context())
    encoded_json = _json.dumps(json).encode("ascii")
    client.request("POST", url, encoded_json, headers=headers)
    response = client.getresponse()
    if not response.status == 200:
        res = response.read()
        print("response was", response.msg, response.headers, response.reason)
        raise Exception(f"Unable to post update to slack: {res}")


def post_extension_published(package_name, version, changelog_content: List[str]):
    """
    Post a message on a hardcoded slack channel about published extension.

    This method can throw an exception if anything fails.
    """
    blocks = []

    # Title & Version
    blocks.append({"type": "header", "text": {"type": "plain_text", "text": f"{package_name} : v{version}"}})

    # Changelog
    changelog = " - ".join(changelog_content).strip(" \n")
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*_changelog_*:\n```{changelog}```"}})

    # Post publish request
    _post(SLACK_HOOK_HOST, SLACK_HOOK_URL, json={"blocks": blocks}, headers={"Content-Type": "application/json"})

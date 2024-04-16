#!/usr/bin/python3.6

# Copyright (c) 2018, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import sys
import ssl
import os
import urllib.parse
import urllib.request

import json

import base64

from pprint import pprint

from nvidia.gitlab.mergerequest import MergeRequest


class Gitlab:

#    url = None
#    auth_token = None

    def __init__(self, url=None, auth_token=None):

        self.url = url
        self.auth_token = auth_token

        if(not self.url):
            raise Exception("'url' parameter must be provided")

        if(not self.auth_token):
            raise Exception("'auth_token' parameter must be provided")

    def get_mr(self, project, mr):
        url = self.url

        url += "/api/v4/projects/" + urllib.parse.quote(project, safe='')
        url += "/merge_requests/" + mr
        url += self._auth_arg()

        return(MergeRequest(json_str=self._call(url)))

    def get_file_content(self, project, f, branch='master'):
        
        url = self.url

        url += "/api/v4/projects/" + urllib.parse.quote(project, safe='')
        url += "/repository/files/" + urllib.parse.quote(f, safe='')
        url += self._auth_arg()
        url += f"&ref={branch}"

        return(base64.b64decode(json.loads(self._call(url))['content']))

    def _call(self, url):
        gcontext = ssl.SSLContext()
        resp = urllib.request.urlopen(url, context=gcontext)
        code = resp.getcode()

        if(code != 200):
            raise Exception(f"Call to `{url}' failed with {code}: " + resp.msg)

        json = resp.read().decode('utf-8')
        return(json)

    def _auth_arg(self):
        return(f"?private_token={self.auth_token}")

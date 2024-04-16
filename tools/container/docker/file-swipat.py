#!/usr/bin/python3.10

import argparse
import base64
import json
import logging
import os
import pprint
import re
import sys
import uuid

import requests

KIND_TO_TEMPLATE_NUM={
    'self-checkout': 2732212,
    #'use-oss': 2885977
    # TODO? "contribute to OSS", let's make sure the simpler 2 options are used responsibly first
}

prompt_placeholder_re=re.compile('([\[][^]]+[\]])', re.MULTILINE)
script_path = os.path.dirname(os.path.realpath(__file__))

def print_debug(s):
  if(args.quiet):
    return
  else:
    print(s)

class NvbugIface:
    def __init__(self, token: str):
        self.token = token

    def save_bug(self, bugdata: dict):
        url = f"https://nvbugsapi.nvidia.com/nvbugswebserviceapi/api/Bug/SaveBug"
        r = requests.post(url, headers={'Authorization': f'Bearer {self.token}', 'Content-type': 'application/json'}, data=json.dumps(bugdata))#, 'Accept': 'text/plain'})
        
        js=r.json()
        print_debug(pprint.pformat((js)))
        print_debug(js["ReturnValue"])
        assert(js["StartIndex"] == 0)
        assert(js["ErrorMessage"] == ""), js["ErrorMessage"]
        #assert(js["TotalCount"] == 1)
        assert(js["EndIndex"] == 0)
        assert(js["IsSuccess"] == True)
        #assert(str(js["ReturnValue"]) == str(bugdata['BugId']))

        return js["ReturnValue"]

    def upload_file(self, bug_id: int, file_path: str):
        file_name = os.path.basename(file_path)
        url = f"https://nvbugsapi.nvidia.com/NVBugsWebServiceApi/api/Bug/UploadFile"
        with open(file_path, 'rb') as f:
            file_data = f.read()
            guid = str(uuid.uuid4())
            payload = {
                "Guid": guid,
                "FileName": file_name,
                "BugID": bug_id,
                "IsPublic": True,
                "Buffer": base64.b64encode(file_data).decode('utf-8'),
            }        
        r = requests.post(url, headers={'Authorization': f'Bearer {self.token}', 'Content-type': 'application/json'}, data=json.dumps(payload))
        js = r.json()
        print_debug(pprint.pformat((js)))

    def get_bug(self, bug_id: int):
        url = f"https://nvbugsapi.nvidia.com/nvbugswebserviceapi/api/bug/getbug/{bug_id}"
        r = requests.get(url, headers={'Authorization': f'Bearer {self.token}'})
        print_debug(r)
        js=r.json()
        print_debug(pprint.pformat((js)))

        assert(js["StartIndex"] == 0)
        assert(js["TotalCount"] == 1)
        assert(js["EndIndex"] == 0)
        assert(js["ErrorMessage"] == ""), js["ErrorMessage"]
        assert(js["IsSuccess"] == True)
        return js["ReturnValue"]

def bug_create(token: str, swipat_kind: str, dependency_name: str, description: str, attachments: list = [], bug_subject_override: str = None):
    assert(swipat_kind in KIND_TO_TEMPLATE_NUM)
    nvbug_template_num=KIND_TO_TEMPLATE_NUM[swipat_kind]

    descr_html = ''
    for line in description.splitlines():
      descr_html += f"{line}<br>\n"
    description = descr_html

    print_debug(f"Description\n--------------------------------------------------\n{description}\n--------------------------------------------------")
    print_debug(f"NVBug template for kind ({swipat_kind}) is {nvbug_template_num}")
    nvbugs = NvbugIface(token)
    nvbug_template_response=nvbugs.get_bug(nvbug_template_num)
    new_bug=nvbug_template_response
    new_bug['IsSubmitted']=1 # XXX <-- critical!
    new_bug['BugId']=0 # https://confluence.nvidia.com/display/NVBUG/SaveBug  "You can create a NEW bug by setting the BugId value as 0 (zero) "

    # https://confluence.nvidia.com/display/NVBUG/SaveBug "HTTP POST Request (simple example to create NEW bugs using only the REQUIRED properties)"
    REQUIRED_FIELDS=[
        "BugId",
        "BugAction",
        "Disposition",
        "IsRestrictedAccess",
        "ApplicationDivisionID",
        "BugTypeID",
        "BugType",
        "Priority",
        "Severity",
        "Synopsis",
        "Description",
    ]
    # Just guessing based on interesting content in GetBug result
    LIKELY_NEEDED_FIELDS=[
        "IsSendNotification",
        "CustomKeywords",
        #"SeeAlsoBugIds",
        "ModuleInfo",
        "BusinessUnits"
        "Origin"
        #"CustomerExtendedProperty"
    ]
    new_bug = {k:v for k,v in new_bug.items() if k in REQUIRED_FIELDS+LIKELY_NEEDED_FIELDS}
    synopsis = bug_subject_override if bug_subject_override else f'SWIPAT: Request to use (via self-checkout) {dependency_name}'
    new_bug['Synopsis'] = synopsis
    new_bug['Description'] = description
    new_bug['BugApplicationIntegration'] = None
    new_bug["GeographicOrigin"] = "US, CA, Santa C"
    new_bug["BusinessUnits"] = "Omniverse"
    new_bug["Origin"] = "Engineering"    
    new_bug_num=nvbugs.save_bug(new_bug)
    print(f"The bug at https://nvbugs.nvidia.com/{new_bug_num} was created.")
    if attachments:
        print(f"Attaching files:")
        for a in attachments:
            nvbugs.upload_file(new_bug_num, a)
            print(f" > {a} attached")
    # Use GetBug API’s response as SaveBug REST API’s request payload – Make sure to edit and set the ‘IsSubmitted’ to 1 before invoking SaveBug API
    # This will ensure that all of your Template Bug’s data will be retained and the isSubmitted = 1 will ensure that the Bug is converted to an actual Bug.
    
    print(f"Please review the bug at https://nvbugs.nvidia.com/{new_bug_num} for accuracy and make changes as needed.")

parser = argparse.ArgumentParser(
                    prog='file-swipat',
                    description='Creates SWIPAT NvBug')
parser.add_argument('-n', '--name', action='store', metavar=('name'), type=str, help='The dependency name')
parser.add_argument('-b', '--bug_subject_override', action='store', metavar=('bug_subject_override'), type=str, help='The SWIPAT bug subject override')
parser.add_argument('-d', '--description-path', action='store', metavar=('description_path'), type=str, help='The path to the file containing description of a SWIPAT bug to be created', required=True)
parser.add_argument('-a', '--attachment', action='append', metavar=('attachment'), type=str, help='The path to the file containing description of a SWIPAT bug to be created')
parser.add_argument('-q', '--quiet', action='store_true', required=0, help='Suppress debug output', default=0)
parser.add_argument('-t', '--token', action='store', metavar=('token'), type=str, help='Token for NvBugs - you can get it at https://nv-auth.nvidia.com/tokens', required=True)
args = parser.parse_args()


# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
import http.client as http_client

if(not args.quiet):
  http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()

if(args.quiet):
  logging.getLogger().setLevel(logging.INFO)
else:
  logging.getLogger().setLevel(logging.DEBUG)

requests_log = logging.getLogger("requests.packages.urllib3")
if(args.quiet):
  requests_log.setLevel(logging.INFO)
else:
  requests_log.setLevel(logging.DEBUG)

requests_log.propagate = True

with open(args.description_path, 'r') as f:
    description = f.read()
    bug_create(token=args.token, swipat_kind='self-checkout', dependency_name=args.name, description=description, attachments=args.attachment, bug_subject_override=args.bug_subject_override)

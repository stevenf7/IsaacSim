#!/usr/bin/env python3.10

import sys

sys.path.insert(0, "../env-bootstrap/lib")

import nvidia.pyenv.bootstrap.v5_0 as env_bootstrap

res = env_bootstrap.bootstrap(
                                runtime_dir='_deps', 
                                pip_requirements_file='pip.requirements.txt',
                                packman_project_file='packman-dependencies.xml',
                                subdirs= 
                                 {
                                   'ovc': ['python'],
                                 }
                               )

from pprint import pprint                               
pprint(res)


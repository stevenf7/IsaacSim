#!/usr/bin/env python3.6

import sys
#import yaml

sys.path.insert(0, "../env-bootstrap/lib")

import nvidia.pyenv.bootstrap.v3_0 as env_bootstrap

env_bootstrap.bootstrap(
                                runtime_dir='_deps', 
                                pip_requirements_file='pip.requirements.txt',
                                packman_project_file='packman-dependencies.xml',
                                subdirs= 
                                 {
                                   'ovc': ['python'],
                                   'omnitools' : 'pylib',
                                 }
                               )

import nvidia.omniverse.client
from pprint import pprint                               

import logging
logging.basicConfig(format="%(message)s", level=logging.INFO)


c = nvidia.omniverse.client.Client(server='ov-sandbox', user='foo', password='foo')
logging.info(c.ping().version)


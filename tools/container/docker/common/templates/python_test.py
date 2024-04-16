#!/usr/bin/env python3.8

################################################################################
## Libs
################################################################################

import sys
import os
from pprint import pprint

bin_path = os.path.dirname(os.path.realpath(__file__))

#sys.path.append(os.path.join(bin_path, "../env-bootstrap/lib"))
#sys.path.append(os.path.join(bin_path, "../lib"))

#import nvidia.pyenv.bootstrap.v3_0 as bootstrap
#
#bootstrap.bootstrap(
#                     runtime_dir='_deps',
#                     pip_requirements_file='test_nvidia_config.requirements.txt',
#                           #   packman_project_file='packman-dependencies.xml',
#                           #    subdirs= 
#                           #      {
#                           #        'ovc': ['python'],
#                           #        'omnitools' : 'pylib',
#                           #      }
#                               )
#

#import nvidia.config

import unittest
import logging 

################################################################################
## Tests
################################################################################

class TestMyStuff(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    logging.basicConfig(format="%(message)s", level=logging.INFO)

  @classmethod
  def tearDownClass(self):
    pass

  def setUp(self):
    pass
  
  def test_sample(self):
    self.assertTrue(1)

################################################################################
## Exec
################################################################################

unittest.main()


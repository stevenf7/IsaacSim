#!/usr/bin/env python3.6

################################################################################
## Libs
################################################################################

import sys
import os 

bin_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(bin_path, "env-bootstrap/lib"))

import nvidia.pyenv.bootstrap.v3_0 as bootstrap

bootstrap.bootstrap(
                     runtime_dir='_deps', 
                     #      pip_requirements_file='pip.requirements.txt',
                     #   packman_project_file='packman-dependencies.xml',
                     #    subdirs= 
                     #      {
                     #        'ovc': ['python'],
                     #        'omnitools' : 'pylib',
                     #      }
                   )

import argparse

from pprint import pprint

################################################################################
## Globals
################################################################################

description = "FIXME program description"
args = None

################################################################################
## Init
################################################################################

def init():
  parse_args()

################################################################################
## Main
################################################################################

def main():
  # do something
  print("Hello world!\n")
    
################################################################################
## Functions
################################################################################

def parse_args():
  #TODO add command line arguments here
  argparser = argparse.ArgumentParser(description=description)

  argparser.add_argument("items", metavar="item", nargs='+', default=None,
                         help="Items on the command line")

  argparser.add_argument("-p", "--parameter", metavar="value",
                         default="none",
                         dest="parameter", 
                         help="Parameter with value"
                        )

  argparser.add_argument("-f", "--flag", 
                          default=False, action='store_true',
                          dest="flag", 
                          help="Flag with no value")

  global args
  args = argparser.parse_args()

################################################################################
## Execute
################################################################################

init()
main()




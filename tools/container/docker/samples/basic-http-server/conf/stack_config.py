#!/usr/bin/python3.6

from pprint import pprint
import logging
import os
import sys
import time

this_dir = os.path.abspath(os.path.dirname(__file__))

# Config loader will call this on load. 
# 
# Avoiding __init__() notation to prevent folks from thinking this is 
# internal Python stuff.

def init():
  pass

################################################################################
# Stack name, services composing this stack, and their ports
################################################################################

# Stack name prefix. Final stack names will be constructed like this:
# {stack_name}_{stack_suffix} where {stack_suffix} comes from stack_suffix_source.
# -n argument to deploy.py is used as STACK SUFFIX. 
stack_name = 'sample'

# Service which image's Family will become the source of the 
# default Stack Suffix
stack_suffix_source = 'sample-http-server'

# These MUST be provided 
required_services = ['sample-http-server' ] 

# These CAN be provided
optional_services = []

# Built-ins are something that's not built, 
# but is typically "just there". 
#
# This is optional. Useful for basic stuff like 
# DockerHub prepackaged things
#
# Represented as tuples (service name, image name)

built_in_services = [ ]

# Functions to obtain built-ins if they're not present. 
# They will receive ONE arg - nvidia.docker object to 
# manipulate Docker.
#
# This is optional

builtins_bootstrap_funcs = { }

# Ports. If not enough of these are available on the target server, deploy will
# fail. Must be a list. Doesn't have to be sequential, or ordered. 

ports = range(8080,8101)  # Note: range() is semantically retarded 
                          # It doesn't include the LAST item into the 
                          # resulting iterable

# Deploy options: will get populated with arguments passed to `-o` of
# deploy.py

deploy_opts = {}

################################################################################
# Data directories 
################################################################################

# Create these additional SUBDIRS in deploy.py's determined 
# root dir on the host. Note that -r option to deploy.py resets the root dir.

data_subdirs = ['log']

################################################################################
# Compose file
################################################################################

# Must return compose file. 
# Inputs (pprint() them to inspect when debugging)
# Note: if using local files in Compose (ie, 'configs:'), !!! USE ABS PATHS ONLY !!!
#
# Args:
#
#  stack_name - string, just the name :) Useful for stuff like network:
#
#  ports - dict, { service_name: port_allocated }, for ports:
# 
#  host_data_dir - string, full path to the HOST directory. 
#                  All your volumes: should go there
#
#  svc_instance_no - dict, { service_name: no_instances }, as provided 
#                    on the command line. Does NOT have ALL services in it, 
#                    just the ones provided on the command line
#
#  images - a dict of dicts; but the important part is: 
#
#       {
#         svc_name:
#          {
#            image: <docker.Image object>
#          }
#       }
#

def get_compose(stack_name, images, ports, host_data_dir, svc_instance_no):

  # I expanded args above to show which ones they are.
  # This func will call a bunch of other funcs underneath,
  # that will need ALL of them, and kwargs notation is just simpler. 

  args = { 'stack_name':  stack_name, 
           'images': images, 
           'ports': ports, 
           'host_data_dir': host_data_dir,
           'svc_instance_no': svc_instance_no
         }

  services_compose = get_services_compose(**args)

  compose_file = f"""
version: "3.3"

services: {services_compose}

networks:

  {stack_name}:

  """

  return(compose_file)

def get_services_compose(**kwargs):
  env_vars = ''

  if('sample-env-var' not in deploy_opts):
    logging.warn("Sample Env Var not set - use 'sample-env-var' deploy opt")
  else:
    env_vars += f"        - OV_SAMPLE_ENV_VAR={deploy_opts['sample-env-var']}\n"

  env_section = ''
  if(len(env_vars)):
   env_section = f"environment:\n{env_vars}"

  ret = f"""
  sample-http-server:
    image: {kwargs['images']['sample-http-server']['image'].tags[0]}
    deploy:
       replicas: 1
       restart_policy:
         condition: on-failure
    {env_section}
    volumes:
        - {kwargs['host_data_dir']}/log:/sample/log
    ports:
        - "{kwargs['ports']['sample-http-server']}:8888"
    networks:
        - {kwargs['stack_name']}
"""

  return(ret)

################################################################################
# Ping, test, and welcome functions
################################################################################

# Can do whatever it wants - once this function returns, 
# deploy.py will assume the stack is at least PARTIALLY up, stable-ish, 
# and will just wait for ALL replicas to show up. 
#
# This is optional, but highly recommended.
# 
# server: server things were deployed to 
# ports, images: same dicts as passed to get_compose() above
#
# Returns boolean pass / fail
#


def wait_for_ping(server, ports, images):
  logging.info("wait_for_ping() is a bit too advanced for this sample")
  logging.info("Use Omniverse CPP Stack Config for a good one")
  logging.info("`omniverse/backend` repo, `docker/stack_configs/ov-cpp.py")

  return(1)


# Can do whatever it wants - this is an optional, "long" test
# function that is explicitly triggered by -t option to deploy.py. 
#
# server and ports args same as above.
#
# Returns boolean pass / fail.
#

def test(server, ports):
  logging.info("test() is a bit too advanced for this sample")
  logging.info("Use Omniverse CPP Stack Config for a good one")
  logging.info("`omniverse/backend` repo, `docker/stack_configs/ov-cpp.py")

  return(1)

# 
# Just prints welcome message. Args should be obvious by now :).
# If not, see above. 
#

def print_welcome(server, ports, images):
  logging.info(f"\n\nDone. Server deployed to {server}, and should be "
               f"listening on tcp/{ports['sample-http-server']}\n")

  logging.info(f"Try this in your browser: " + 
               f"http://{server}:{ports['sample-http-server']}")


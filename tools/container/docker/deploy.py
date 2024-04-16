#!/usr/bin/env python3.10

################################################################################
## Libs
################################################################################

import os
import sys

bin_path = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, bin_path + "/common/lib")
sys.path.insert(0, bin_path + "/lib")

import argparse
import collections
import glob
import json
import logging
import re
import socket
import subprocess
import time
import urllib
from pprint import pprint

import nvidia.docker
import nvidia.docker.registry.argparse
import nvidia.docker.stack
import yaml
from nvidia import config_loader
from nvidia.die import die
from nvidia.sysutils import pop_dir_pos, push_dir_pos, reset_dir

################################################################################
## Globals
################################################################################

description = "Deploys Omniverse to a Docker server"
args = None

docker = None

work_dir = f"{bin_path}/__deploy"
stack_config_work_dir = os.path.join(work_dir, "stack_config_work_dir")
host_data_root = "/var/lib/omni"

Ingress = collections.namedtuple("Ingress", ["host", "port", "path", "url"])



################################################################################
## Init
################################################################################

def init():
  logging.basicConfig(format="%(message)s", level=logging.INFO)

  parse_args()
  reset_dir(work_dir)
  reset_dir(stack_config_work_dir)


  global docker
  docker = init_docker_conn()

################################################################################
## Main
################################################################################

def main():
  logging.info(f"Loading config from {args.stack_config}")
  stack_config = config_loader.get_configs([args.stack_config])[0].config

  populate_deploy_options(stack_config)

  if(hasattr(stack_config, 'docker')):
    stack_config.docker = docker
  if(hasattr(stack_config, 'prepare')):
    stack_config.prepare()

  logging.info(f"Will be deploying to: {args.server}")

  service_images = prepare_images(args, stack_config)

  # I need images and config loaded before I can check if args are sane
  # (specifically, -i for counts and -t for running tests)

  if(not check_args(args, stack_config, service_images)):
    sys.exit(1)

  stack_name  = get_stack_name(stack_config, args, service_images)

  logging.info(f"Stack name: {stack_name}")

  logging.info(f"Determining ports")
  ports = get_ports(stack_name, service_images, stack_config)

  if(not args.dry_run):
    docker.remove_stack(stack_name, print_callback=logging.info)

  host_data_dir=f"{host_data_root}/{stack_name}"
  prepare_host_datadir(host_data_dir, stack_config, args)

  compose_file_str = stack_config.get_compose(stack_name=stack_name,
                                         images=service_images, 
                                         ports=ports,
                                         host_data_dir=host_data_dir,
                                         svc_instance_no=args.svc_instance_no
                                        )
  
  compose_file = f"{work_dir}/docker-compose.yml"
  with open(compose_file, "w") as cfh:
    cfh.write(compose_file_str)

  if(args.dry_run):
    logging.info("---")
    logging.info("This is a dry run.")
    logging.info(f"Compose file saved to {compose_file}")
    logging.info(f"It's contents below")
    logging.info("---")
    logging.info(compose_file_str)
    sys.exit(0)

  docker.deploy_stack(compose_file=compose_file, 
                      name=stack_name)

  logging.info("---")

  stack = nvidia.docker.stack.Stack(docker, stack_name)
  inspect_stack(stack, service_images)
  wait_for_ping(stack_config, server=args.server, 
                              ports=ports, 
                              images=service_images)
  logging.info("---")
  wait_till_stack_is_up(stack)

  if(args.test):
    logging.info("Running tests")
    print("-"*70)
    ret = stack_config.test(args.server, ports)
    print("-"*70)
    if(not ret):
      logging.error("Tests failed")
      sys.exit(1)
    else:
      logging.info("Tests succeeded")

  if(hasattr(stack_config, 'print_welcome')):
    stack_config.print_welcome(args.server, ports, service_images)
  else:
    logging.info(f"\n\nDone. But {args.stack_config} doesn't provide " + 
                  "print_welcome() func.\nHow rude.")

  sys.exit(0)

  
################################################################################
## Functions
################################################################################

def prepare_host_datadir(datadir, config, args):
  logging.info(f"Preparing host data dir at {datadir}")

  delete_list = []

  if(args.reset_data):
    logging.info(" > Deleting existing host data directory, you asked for it!!!")
    delete_list = [datadir]
  elif(len(args.reset_subdirs)):
    logging.info(f" > Deleting following host data subdirs, you asked for it!!!")
    for d in args.reset_subdirs:
      logging.info(f"   {datadir}/{d}")
      delete_list.append(f"{datadir}/{d}")

  if(len(delete_list) and (not args.dry_run)):
    docker._delete_hostdir(delete_list)

  dirs = [ datadir ]

  if(hasattr(config, 'data_subdirs') and len(config.data_subdirs)):
    logging.info(" > Will create these additional dirs:")
    for sd in config.data_subdirs:
      dir = f"{datadir}/{sd}"
      dirs.append(dir)
      logging.info(f"   {dir}")

  if(not(args.dry_run)):
    docker._create_hostdir(dirs)

def wait_for_ping(stack_config, **kwargs):
  if(not hasattr(stack_config, 'wait_for_ping')):
    logging.info(f"{args.stack_config} does not provide " + 
                 f"wait_for_ping() - proceeding")
    return

  logging.info(f"Waiting for ping with wait_for_ping() from {args.stack_config}")

  ret = stack_config.wait_for_ping(server=kwargs['server'],
                                   ports=kwargs['ports'], 
                                   images=kwargs['images'])
  if(not ret):
    logging.error("Waiting failed")
    sys.exit(1)
  else:
    return()

def grep_services_requiring_ports(service_images):

  ret = []

  for svc, image in service_images.items():
    port = image_port(svc, service_images[svc]['image'])

    if(port):
      ret.append(svc)
    else:
      pass

  return(ret)

def image_port(svc, image):

  cont_conf = image.attrs['ContainerConfig']
  if 'ExposedPorts' in cont_conf:
    ports = list(cont_conf['ExposedPorts'].keys())
    port = ports[0].replace("/tcp", "")

    if(len(ports) != 1):
      logging.warning(f"  > {svc} exposes more than one port") 
      if(args.allow_multi_port):
        logging.info(f"   > will only process {port}")
      else:
        logging.error(f" > can't proceed.")
        sys.exit(1)
    else:
      logging.info(f"  > {svc} requires tcp/{port} to be exposed")

    return(port)
  else:
    logging.info(f"  > {svc} does not need a port to be exposed")
    return None

def determine_stack_ports(stack, service_images):
  ret = {}

  name_map = dict(map(lambda x: (f"{stack.name}_{x}", x), service_images.keys()))
  
  for service in stack.services():
    ports = service.ports()
    if(len(ports)):
      service_name = name_map[service.api.name]
      logging.info(f"   > Service '{service_name}' already running " + 
                   f"on {ports[0]}, reusing")

      ret[service_name] = ports[0]
      if(len(ports) != 1):
        logging.warning(f"   > found more ports, but only {ports[0]} will " +   
                         "be reused")
  return(ret)


def get_ports(stack_name, service_images, stack_config):

  if(isinstance(stack_config.ports, list)):
    logging.warning("  > Your stack is using the old ports notation.")
    logging.warning("  > Please consider switching to new one in the " +    
                    "YAML format.")
    return(get_ports_legacy(stack_name, service_images, stack_config))
  elif(isinstance(stack_config.ports, dict)):
    return(get_ports_next_gen(stack_name, service_images, stack_config.ports))
  elif(isinstance(stack_config.ports, str)):
    logging.info("  > `ports` is a string, assuming YAML")
    return(get_ports_next_gen(stack_name, service_images, 
                              yaml.safe_load(stack_config.ports)))
    
  else:
    logging.error("`ports` variable in your stack config is of " + 
                  "an unrecognized type - should be string, array, or dict")

    sys.exit(1)

def get_ports_next_gen(stack_name, service_images, port_requests):
  logging.info("  > determining current ports allocation")

  used_ports = []
  existing_stack = None

  for st in docker.get_stacks():
    if(st.name == stack_name):
      existing_stack = st
    else:
      for s in st.services(): 
        used_ports += s.ports()

  for (service, ports) in port_requests.items():
    logging.info(f"  > allocating ports for {service}")
    for (port_name, port_config) in ports.items():
      current_ports = get_current_ports(service, existing_stack)
      logging.info(f"    > {port_name}, container port " + 
                   f"{port_config['container']}")

      if(port_config['container'] in current_ports):
        current_port = current_ports[ port_config['container'] ]
        logging.info(f"      > reusing already allocated host port " + 
                     f"{current_port}")
        port_config['allocated'] = current_port
      else:
        logging.info(f"      > attempting to allocate a new host port")
        port_config['allocated'] = allocate_new_port(port_config, used_ports)

  return(port_requests)

def allocate_new_port(config, used):
  for port in config['host']:
    if(port in used):
      logging.info(f"        > {port}: already in use")
    else:
      logging.info(f"        > {port}: avaliable!")
      return(port)

  logging.error(f"        > Unable to find an unused port from the list of "
                 "desired ones, giving up")
  sys.exit(1)
     

def get_current_ports(service_name, stack):
  if not(stack):
    return({})

  for service in stack.services():
    if(service.info['image_name'].startswith(f'{service_name}:')):
      return(service.ports_map())

  return({})
  
def get_ports_legacy(stack_name, service_images, stack_config):

  services_with_ports = grep_services_requiring_ports(service_images)
  
  used_ports = []
  existing_stack_ports = {}

  for st in docker.get_stacks():
    for s in st.services(): 
      used_ports += s.ports()

    if(st.name == stack_name):
      existing_stack_ports = determine_stack_ports(st, service_images)

  cur_port_idx = 0
  allocated_ports = []
  n_ports_needed =  len(services_with_ports) - len(existing_stack_ports)

  used_ports_kv = {p:p for p in used_ports}
  while ((cur_port_idx < len(stack_config.ports)) and n_ports_needed):
    cur_port = stack_config.ports[cur_port_idx]
    if (cur_port not in used_ports_kv):
      allocated_ports.append(cur_port)
      n_ports_needed -= 1
    cur_port_idx += 1

  logging.info(f"  > allocated new ports {allocated_ports}")

  if(n_ports_needed):
    logging.error(f"  > Couldn't find enough ports: still need " + 
                  f"{n_ports_needed} ports, giving up")
    sys.exit(1)

  logging.info(f"  -----")
  ret = {}

  for svc in services_with_ports:
    if (svc in existing_stack_ports):
      ret[svc] = existing_stack_ports[svc]
    else:
      ret[svc] = allocated_ports.pop(0)
    
    logging.info(f"  > {svc} will be accessible on {ret[svc]}")

  return(ret)

def get_stack_name(stack_config, args, images):
  suffix = None
  if(args.stack_name_suffix):
    suffix = args.stack_name_suffix
  else:
    if(stack_config.stack_suffix_source):
      image = images[stack_config.stack_suffix_source]['image']
      suffix = image.labels['com.nvidia.omniverse.build.family']
    else:
      logging.error("\n")
      logging.error("Your Stack Config does not specify source for")
      logging.error("Stack Name Suffix. That's okay, but make sure")
      logging.error("to specify one using -n <desired suffix>")
      logging.error("command line argument")
      sys.exit(1)

  return(f"{stack_config.stack_name}-{suffix}")

def prepare_images(args, stack_config):

  logging.info('Preparing images')

  if(args.registry):
    ret = load_registry_images(args, stack_config)
  else:
    ret = load_local_images(args, stack_config)

  # "Built in" images
  if(not hasattr(stack_config, 'built_in_services')):
    return(ret) 
  if(not len(stack_config.built_in_services)):
    return(ret)

  logging.info(f"  > Loading required internal images")
  intstr = '__internal__'

  internal_img_dict = {}

  for svc, image_name in stack_config.built_in_services:
    logging.info(f"   > Looking for image for {svc} ({image_name})")
    if(image_name in internal_img_dict):
      logging.info(f"    > already found before")
    else: 
      if not docker.image_exists(full_name = image_name):
        logging.info(f"    > {image_name} not found, attempting to obtain...")
        image = obtain_internal_image(stack_config, image_name)
        if not (image):
          logging.error(f"Can't continue: fix your config, and retry")
          sys.exit(1)
        internal_img_dict[svc] = image
      else:
        logging.info(f"    > {image_name} found")
        internal_img_dict[svc] = docker.api.images.get(image_name)

    ret[svc] = service_entry(internal_img_dict[svc], intstr)

  exit_fail = 0
  for required_service in stack_config.required_services:
    if required_service not in ret:
      logging.info(f"!!! Image for service '{required_service}' " +
                    "was not provided !!!")
      exit_fail = 1

  if exit_fail:
    sys.exit(1)

  return(ret)

def load_registry_images(args, stack_config):
  logging.info(f"  > Loading images from {args.registry}")

  ret = {}

  for svc in stack_config.required_services + stack_config.optional_services:
    if args.images[0] == '@':      
      logging.error("You pointed '@' along with 'registry' option. Please point registry tag instead.")
    image_fullname = f"{args.registry}/{svc}:{args.images[0]}"
    logging.info(f"   > Pulling {image_fullname}") 
    image = None
    try:
      image = docker.api.images.pull(image_fullname)
    except Exception as e:
      logging.error(" ")
      logging.error("Pulling image failed, Docker says:")
      logging.error(" ")
      logging.error(str(e))
      sys.exit(1)

    ret[svc] = service_entry(image, args.registry)

  return(ret)

def load_local_images(args, stack_config):
  img_list = args.images
  img_dict = dict(map(lambda x: (x,x), img_list))

  ret = {}

  # Most recents
  if('@' in img_dict):
    ret = load_most_recent_images(stack_config)
    img_dict.pop('@')

  # Expand globs  - because Windows is dumb. 
  for entry in list(img_dict.keys()):
    globbed = glob.glob(entry)
    if(len(globbed)):
      img_dict.pop(entry)
      img_dict.update(list(map(lambda x: (x,x), globbed)))

  # Just strings in list of images
  for entry in list(img_dict.keys()):
    if(os.path.isfile(entry)):
      continue
    
    logging.info(f"  > Processing name arg: {entry}")
    image = image_from_name(entry)
    check_same_service_exists(ret, svcname(image))

    ret[svcname(image)] = service_entry(image, entry)
    img_dict.pop(entry)

  # Finally, files
  for entry in img_dict.keys():
    logging.info(f"  > Processing file arg: {entry}")

    svc_name = svcname_tar(entry)
    check_same_service_exists(ret, svc_name)

    image = upload_image(entry)
    ret[svc_name] = service_entry(image, entry)

  return(ret)


def svcname_tar(path):
  tar_image = nvidia.docker.tarimage.TarImage(path)
  svcname = tar_image.label('com.nvidia.omniverse.service')

  if not svcname:
    raise Exception(f"Something's wrong with image at {path}: no " + 
                     "service name defined!")

  return(svcname)

def svcname(image):
  return(image.labels['com.nvidia.omniverse.service'])

def check_same_service_exists(svcmap, service_name):
  if(service_name in svcmap):
    logging.info(f"   > service '{service_name}' already loaded via " + 
                 f"'{svcmap[service_name]['arg']}' argument you supplied")

    if args.allow_dup_image_args:
      logging.info( "   > it will be replaced by this one")
    else:
      logging.info(" !!!! fix image list, and re-run !!!!")
      sys.exit(1)

def load_most_recent_images(stack_config):
  logging.info('  > Checking most recent images')

  ret = {}

  for svc_name in stack_config.required_services + stack_config.optional_services:
    mri_file = f"{bin_path}/__most_recent_image_{svc_name}"
    if(os.path.isfile(mri_file)):

      image_name = None
      with open(mri_file, 'r') as fh: 
        image_name = fh.read()

      logging.info(f"   > found {image_name}") 
      ret[svc_name] = service_entry(image_from_name(image_name), '@')

  return(ret)

def service_entry(image, arg):
  return( { 'image': image, 'arg': arg } )

def image_from_name(name):
  ret = None

  if not (docker.image_exists(full_name=name)):
    logging.error(f"   > Image '{name}' not found on the server!")
    sys.exit(1)
  else:
    ret=docker.api.images.get(name)

  check_image(ret)
  return(ret)

def check_image(image):

  required_labels = ['com.nvidia.omniverse.build.family',
                     'com.nvidia.omniverse.build.release', 
                     'com.nvidia.omniverse.build.build', 
                     'com.nvidia.omniverse.service']

  for l in required_labels:
    if l not in image.labels:
      raise Exception(f"Something's wrong with the image: it doesn't have " + 
                      f"the '{l}' label")
  

def upload_image(path):
  logging.info(f"   > Uploading image from {path}...")
  ret=docker.upload_image(path, return_existing=True)
  check_image(ret)
  return(ret)

def check_args(args, stack_config, images):
  ret = 1

  if(args.test):
    if(not hasattr(stack_config, 'test')):
      logging.error(f"You asked me to run tests, but " + 
                    f"{args.stack_config} does not provide")
      logging.error("test() function")
      ret = 0
  
  if(len(args.svc_instance_no)):
    for (svc, count) in args.svc_instance_no.items():
      if(svc not in images):
        ret = 0
        logging.error(f"You asked for {count} instances of {svc}, but {svc} " + 
                       "is not a valid service in this config.")
        logging.error(f"Here are the valid ones:\n " +
                       "\n ".join(sorted(images.keys())))
  return(ret)

def parse_args():
  argparser = argparse.ArgumentParser(description=description)

  argparser.add_argument("images", metavar="image", nargs='*', default=None,
                         help="Images to deploy (filename, image name, @ " + 
                              "for most recent ones, or registry tag).",
                        )

  argparser.add_argument("-s", "--server", metavar="server",
                         dest="server", 
                         required=1,
                         help="Server to deploy to"
                        )

  argparser.add_argument("-c", "--config", metavar="file",
                          dest="stack_config", 
                          required=1,
                          help="Stack configuration file"
                        )

  argparser.add_argument("-n", "--name", metavar="suffix",
                          default=None,
                          dest="stack_name_suffix", 
                          help="Stack name suffix (defaults to image family)"
                        )

  argparser.add_argument("-i", "--instances", 
                          action='append',
                          metavar="<SERVICE>:<COUNT>",
                          default=[],
                          dest="svc_instance_no", 
                          help="Number of instances for a given service" + 
                               " (multiple -i options okay)"
                        )

  argparser.add_argument("-in", "--ingress", 
                          dest="ingress",
                          default=None,
                          help="Ingress router host and root path"
                        )


  argparser.add_argument("-o", "--deploy-option", 
                          action='append',
                          metavar="<OPTION>:<VALUE>",
                          default=[],
                          dest="deploy_opts", 
                          help="Deploy options (will be passed to Stack Config " + 
                               "as a dictionary). " +
                               "(multiple -o options okay)"
                        )

  argparser.add_argument("--run-tests", "--test", 
                          default=False, action='store_true',
                          dest="test", 
                          help="Run unit tests after the stack comes up"
                        )

  argparser.add_argument("--ssh", 
                          default=False, action='store_true',
                          dest="ssh", 
                          help="Use SSH to connect to Docker"
                        )

  argparser.add_argument("-t", "--tag", 
                         metavar="TAG",
#                          default=False, action='store_true',
                          dest="registry_tag", 
                          help="Use this registry tag when selecting images"
                        )

  argparser.add_argument("--reset", 
                          default=False, action='store_true',
                          dest="reset_data", 
                          help="Reset (delete and recreate) root data dir on " +
                               "target host"
                        )

  argparser.add_argument("--reset-subdir", 
                          action='append',
                          metavar="DIR",
                          default=[],
                          dest="reset_subdirs", 
                          help="Reset specific subdirs (relative to root data " + 
                               "dir) on target host (multiple " +
                               "--reset-subdir options okay)"
                        )

  argparser.add_argument("-d", "--dry", 
                          default=False, action='store_true',
                          dest="dry_run", 
                          required=0,
                          help="Dry run (don't do anything)"
                        )

  argparser.add_argument("--allowdups",
                          default=False, action='store_true',
                          dest="allow_dup_image_args", 
                          help="Allow duplicate service images in the " + 
                               "list of images. Order of priority: " + 
                               "file overrides name overrides most recent (@)"
                        )

  argparser.add_argument("-mp", "--allow-multi-port", 
                          default=False, action='store_true',
                          dest="allow_multi_port", 
                          required=0,
                          help="Allow multi-port images (still only the FIRST " + 
                               "ONE will get exposed)" 
                        )

  nvidia.docker.registry.argparse.add_registry_args(argparser, "registry")

  global args
  args = argparser.parse_args()

  err = nvidia.docker.registry.argparse.parse_registry_args(args, "registry")
  if(err):
    logging.error(err)
    sys.exit(1)

  if(not os.path.isfile(args.stack_config)):
    logging.error(f"Error parsing '-c {args.stack_config}'")
    logging.error(f"\"{args.stack_config}\" is not a file\n")
    logging.error(f"-c argument no longer means 'count', it's now used to")
    logging.error(f"provide path to the Stack Config file.\n")
    logging.error(f"Run with --help, or check README.md")
    sys.exit(1)

  svc_nos = {}

  try:
    svc_nos = dict([ x.split(':') for x in args.svc_instance_no ])
  except Exception as e:
    logging.error(f"Error parsing -i options: make sure they follow " +  
                   "-i <service_name>:<count> notation, " + 
                   "i.e., -i omniverse:10")

    logging.error(f"You've provided: " +
                   " ".join(f"-i {x}" for x in args.svc_instance_no))
    sys.exit(1)

  args.svc_instance_no = svc_nos

  if(args.ingress):
    args.ingress = parse_ingress(args.ingress)
    logging.info("Ingress path normalized to:")
    logging.info("  > host: " +  args.ingress.host)
    logging.info("  > port: " +  args.ingress.port)
    logging.info("  > path: " +  args.ingress.path)

  if(args.registry):
    if(args.registry_tag):
      if(len(args.images) != 0):
        logging.error("You must specify tag EITHER as -t value, or as an " + 
                      "image selector")
        sys.exit(1)
      else:
        args.images.append(args.registry_tag)

    if(len(args.images) > 1):
      logging.error("When using a registry, you can only provide one tag")
      sys.exit(1)

    if(not len(args.images)):
      logging.error("When using registry, you must provide a tag - either as" + 
                    "an image arg, or as a value to -t option")

    if(args.images[0] == 'latest'):
      logging.error("You can NOT use the 'latest' tag, please use exact " +  
                    "version number instead")
      sys.exit(1)
  elif(not len(args.images)):
    logging.error("No image selectors were supplied - can't continue")
    sys.exit(1)

def parse_ingress(ingress):
  if(not re.search("^\w+://", ingress)):
    ingress = f"https://{ingress}"

  parsed = urllib.parse.urlparse(ingress)

  if(parsed.scheme != "https"):
    die(f"Scheme {ret.scheme} not supported for ingress, please use HTTPS")

  (host, port) = (None, None)
  if(":" in parsed.netloc):
    (host, port) = parsed.netloc.split(":")
  else: 
    host = parsed.netloc
    port = 443

  path = parsed.path.rstrip("/").lstrip("/")
  if(not len(path)):
    path = '/'

  url = f"{host}"
  if(port != 443):
    url += f":{str(port)}"
  if(path != '/'):
    url += f"/{path}"

  ret = Ingress(host, str(port), path, url)
  return(ret)

def init_docker_conn():
  server = None

  if(args.ssh):
    logging.info("Using SSH to connect to server")
    server = f"ssh://{args.server}"
  else:
    logging.info("Using TCP to connect to server")
    server = args.server

  conn = nvidia.docker.Docker(server=server)
  return(conn)

def obtain_internal_image(stack_config, image):
  if(hasattr(stack_config, 'builtins_bootstrap_funcs')):
    builtins_bootstraps = stack_config.builtins_bootstrap_funcs
    if isinstance(builtins_bootstraps, dict):
      if(image in builtins_bootstraps):
        func = builtins_bootstraps[image]
        return(func(docker))
      else:
        logging.error(f"    > 'builtins_bootstrap_funcs' doesn't provide " + 
                     f"a func to bootstrap {image}")
        return(None)
    else:
      logging.error(f"    > 'builtins_bootstrap_funcs' must be a dict")
      return(None)
  else:
    logging.error(f"    > stack config doesn't provide 'builtins_bootstrap_funcs'")
    return(None)
    
  sys.exit(0)

def inspect_stack(stack, images):

  logging.info("Inspecting stack")
  
  # Just a deep copy
  expected_services = dict(images)
  
  # Services in the Stack are called <stack_name>_<service_name>.
  # We're gonna trim "stack_name_" to compare to our internal list of 
  # services with images

  trim_l = len(stack.name) + 1

  for svc in stack.services():
    name = svc.info['name'][trim_l:]

    if(name in expected_services):
      logging.info(f"  > {name}: present as {svc.info['name']}, " + 
                   f"{svc.info['n_required']} replicas")
      del expected_services[name]
    else:
      logging.warning(f"  > {name}: looks like was dynamically added.")
      logging.warning(f"  > That's okay, just make sure you intended this.")

  for missing_svc in expected_services.keys():
    logging.warning(f"  > !!! {missing_svc} not found in just deployed stack !!!")
    logging.info(f"  > Please make sure this is intended")
    
def wait_till_stack_is_up(stack):
  logging.info("Waiting for all service replicas to come up...")

  terminate = 0
  skip = {}

  while(not terminate):

    terminate = 1
    time.sleep(1)
    stack.refresh()

    for svc in stack.services():
      if(svc.info['id'] in skip):
        continue
      n_req = svc.info['n_required']
      n_up = svc.info['n_up']
      logging.info(f"  > {svc.info['name']}: {n_up}/{n_req} up")
      if(n_up < n_req):
        terminate = 0
      elif(n_up == n_req):
        skip[svc.info['id']] = 1
      else:
        raise Exception("Shouldn't be here")

    if(terminate):
      break 

  return

def populate_deploy_options(stack_config):

  if(not hasattr(stack_config, 'deploy_opts')):
    logging.warn("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    logging.warn("!! Your stack does not have deploy_opts defined. It's     !!")
    logging.warn("!! okay, but consider adding it asap - it's useful.       !!")
    logging.warn("!! Check out -o deploy option.                            !!")
    logging.warn("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    return
    
  stack_config.deploy_opts = parse_dep_opts_arg(args.deploy_opts)
  stack_config.deploy_opts['_server'] = args.server
  stack_config.deploy_opts['_reset_data'] = args.reset_data
  stack_config.deploy_opts['_work_dir'] = stack_config_work_dir
  if(args.ingress):
    stack_config.deploy_opts['_ingress'] = args.ingress

def parse_dep_opts_arg(opt_arr):
  ret = {}

  for opt in opt_arr:
    split = opt.split(":")
    if(len(split) < 2):
      logging.error(f"Malformed deploy option: >{opt}<")
      logging.info("Format: <option name>:<value>")
      sys.exit(1)
    
    name = split.pop(0)
    ret[name] = ":".join(split)

  return(ret)
################################################################################
## Execute
################################################################################

init()
main()

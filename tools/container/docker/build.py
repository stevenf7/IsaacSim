#!/usr/bin/env python3.10

################################################################################
## Libs
################################################################################

import sys
import os 

bin_path = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, f"{bin_path}/common/lib")
sys.path.insert(0, bin_path + "/lib")

import argparse

import importlib.util

from pprint import pprint
import socket
import getpass
from time import localtime, strftime

import io
import shutil
import re
import subprocess

import glob

import nvidia.docker
import logging 
import subprocess

from nvidia.sysutils import reset_dir, push_dir_pos, pop_dir_pos
from nvidia import config_loader
from nvidia.die import die

import nvidia.gitlab.utils

import nvidia.git
import nvidia.gitlab.ci

import nvidia.build.versioning
from nvidia.build.versioning import norm_string

from nvidia.docker.utils.imglist_parser import parse_image_list
import nvidia.docker.utils.policy

################################################################################
## Globals
################################################################################

VERSION = "1.3.0"

LABEL_MARKER = '__NV_DOCKER_BUILD INSERT_LABELS_HERE'
BASE_IMAGE_NAME_PREFIX = '__NV'

description = "Builds an Omniverse Docker image"
args = None

work_dir = f"{bin_path}/__build"
code_root = os.path.realpath(f"{bin_path}/../")

base_images = []

docker = None

class defaults:
  family = 'local'
  no_version = 'no_version'
  default_release="private"
  default_base_image_list = os.path.join(bin_path, "approved_base_images")
  default_version_file="../../VERSION.md" # relative to image config
  repo_root_rel ="../../" # relative to image config

################################################################################
## Init
################################################################################

def init():
  logging.basicConfig(format="%(message)s", level=logging.INFO)

  nvidia.die.settings.log = 1
  nvidia.die.settings.stderr = 0


  parse_args()
  global docker
  docker = init_docker_conn()

  global base_images
  logging.info("Loading base image list from " +    
              f"{defaults.default_base_image_list}")
  base_images = parse_image_list(defaults.default_base_image_list)

  if(args.dump_env):
    logging.info("Current environment:")
    for n in sorted(os.environ.keys()):
      logging.info(f"  > {n}: {os.environ[n]}")


################################################################################
## Main
################################################################################

def main():

  logging.info("Code root: %s" % code_root)

  build_report = { "build_server": args.server if args.server else "__local__",
                   "build_py_version": VERSION, 
                   "command_line": " ".join(sys.argv),
                   "images": []
                 }
                 
  for build_config in (config_loader.get_configs(args.configs)):
    built_services = {}
    report_entry = {}
    logging.info("*"*75)
    logging.info(f"Processing config at {build_config.path}")
    service_name = build_config.config.service_name

    if(service_name in built_services):
      die(f"Service {build_config.config.service_name} already built:" +
            " looks like duplicate configs were passed in!")

    reset_dir(work_dir)

    cache_images = []

    if(len(args.cache_tags)):
      logging.info("  > Cache tags specified, attempting to determine cache " + 
                   "registry")
      cache_registry = get_cache_registry(build_config.path)
      logging.info("  > Will use these images for build cache:")
      for tag in args.cache_tags:
        i = f'{cache_registry}/{service_name}:{tag}'
        logging.info(f'    > {i}')
        cache_images.append(i)

    image = build(build_config, cache_images=cache_images)

    report_entry = { 
                     "service_name": service_name, 
                     "image": image.tags[0] if image else None,
                     "image_id": image.id if image else None,
                   }
    built_services[service_name] = service_name
    build_report['images'].append(report_entry)


  if(args.generate_report):
    import json 
    print(json.dumps(build_report))

################################################################################
## Functions
################################################################################

def populate_built_in_base_images(dockerfile_str):
  markers_found = 0
  
  ret = ''
  logging.info("  > scanning dockerfile for base image markers")

  line_no = 1

  for line in dockerfile_str.splitlines():
    if('FROM' in line):
      for img in base_images.values():
        marker = "_".join([BASE_IMAGE_NAME_PREFIX, img.name])
        if(marker in line):
          logging.info(f"    > found {marker}, line #{line_no}")
          logging.info(f"    > corresponding image: {img.full_name}")
          line = line.replace(marker, img.full_name)
          break

    ret += f"{line}\n"
    line_no += 1

  return(ret)

def build(build_config, cache_images=[]):

  logging.info(f"  > Service name: {build_config.config.service_name}")

  repo_root = os.path.dirname(build_config.path)
  repo_root = os.path.join(repo_root, defaults.repo_root_rel)
  repo_root = os.path.abspath(repo_root)

  logging.info(f"  > Repo root: {repo_root}")


  release = nvidia.build.versioning.get_release(repo_root)
  branch = nvidia.build.versioning.get_branch(repo_root)
  build = nvidia.build.versioning.get_build(repo_root, build_no=args.build_no)

  version_full = nvidia.build.versioning.get_version_full(release=release,    
                                                          family=args.family, 
                                                          build=build, 
                                                          branch=branch)

  image_tag = nvidia.build.versioning.get_docker_image_tag(release=release,    
                                                           family=args.family, 
                                                           build=build, 
                                                           branch=branch)

  logging.info(f"  > full version to be assigned: `{version_full}`")
  logging.info(f"  > image tag: `{image_tag}`")
  image_fullname = build_config.config.service_name + ":" + image_tag
  logging.info(f"  > target image name: `{image_fullname}`")

  # Removed due to OmniFlow
#  if(docker.image_exists(full_name=image_fullname)):
#    raise Exception("Image with this name already exists on the server, " +
#                    "cowardly giving up")

  out_file = get_outfile_path(build_config.config.service_name, image_tag)
  if(out_file):
    logging.info("  > Output to: %s" % out_file)
  else:
    logging.info("  > Will not be saving image file")

  # This following section is ugly - backwards compatibility galore... 
  # I really need to rewrite this whole setup; but not yet...
  func_args = get_dockerfile_func_args(build_config.config.dockerfile, 
                                       release=release,
                                       family=args.family,
                                       build=build)


  dockerfile = build_config.config.dockerfile(**func_args)
  dockerfile = populate_built_in_base_images(dockerfile)

  labels = get_build_id_labels(build_config=build_config, 
                               release=release,
                               family=args.family,
                               build=build, 
                               branch=branch)

  if(args.enforce_compliance):
    compliance_labels = check_compliance(dockerfile)
    labels.extend(compliance_labels)
  else:
    logging.info("  > will not apply compliance policies")
    labels.append(non_compliant_label())

  dockerfile = add_labels(dockerfile, labels)

  if(args.dry_run):
    logging.info("  > This is a dry run, will stop now")
    logging.info("  > Here is the Dockerfile that would have been used:")
    logging.info("--------------------------------------------------")
    print(dockerfile)
    logging.info("--------------------------------------------------")
    return

  logging.info("  > Copying code to build dir...")
  copy_code(build_config, work_dir)
  set_version(work_dir, version_full)

  dockerignore = get_dockerignore(build_config)

  if(dockerignore):
    di_out = f"{work_dir}/.dockerignore"
    with open(di_out, "w") as h:
      h.write(dockerignore)
    logging.info(f"  > .dockerignore saved to {di_out}")

  if(args.damp_run):
    logging.info( "  > This is a damp run, will stop now")
    logging.info(f"  > build dir at {work_dir}")
    df_out = f"{work_dir}/Dockerfile"
    with open(df_out, "w") as dfh: 
      dfh.write(dockerfile)
    logging.info(f"  > Dockerfile saved to {df_out}")
    return

  logging.info("  > Building...")

  docker.build_image(image_fullname, build_in=work_dir, 
                                     dockerfile=dockerfile, 
                                     keep_dockerfile=True,
                                     plain_progress=args.plain_progress,
                                     cache_from=cache_images, 
                                     no_buildkit=args.no_buildkit,)
 
  with open(f"{bin_path}/__most_recent_image_{build_config.config.service_name}", 
            'w') as fh:
    fh.write(image_fullname)

  if(args.save_image_file):
    logging.info("  > Saving...")
    docker.save_image(image_fullname, out_file)
    logging.info(f"  > Saved to {out_file}")

  image = docker.api.images.get(image_fullname)
  return(image)

def get_version_full(release, family, build, branch):
  return(f"{release}+{branch}.{family}.{build}")

def add_labels(dockerfile, labels):
  logging.info("  > checking dockerfile, adding labels")

  lines = []
  idx = 0
  last_from_idx = -1
  marker_idx = -1

  for line in dockerfile.splitlines():
    check_is_an_offending_label(line)

    if('FROM' in line):
      last_from_idx = idx

    if(LABEL_MARKER in line):
      logging.info(f"  > {LABEL_MARKER} found, will insert labels after it")
      marker_idx = idx
    else:
      lines.append(line)

    idx += 1

  append_at_idx  = marker_idx if marker_idx >= 0 else last_from_idx+1
  ret = lines[:append_at_idx]

  for l in labels:
    logging.info(f"    > {l}")

  ret.extend(labels)

  ret.extend(lines[append_at_idx:])

  return("\n".join(ret))

def non_compliant_label():
  return(f"LABEL {compliance_label()}=0")

def check_compliance(dockerfile):
  logging.info("  > applying compliance policies")

  (result, labels) = nvidia.docker.utils.policy.check_compliance(dockerfile, 
                                            approved_bases=base_images.values())
  if(not result):
      die("Compliance check failed")
  
  labels.append(f"LABEL {compliance_label()}=1")
  return(labels)
  
def compliance_label():
  return("com.nvidia.omniverse.build.compliant")

def get_build_id_labels(build_config, release, family, build, branch):
  ret = []

  ret.append(f"LABEL com.nvidia.omniverse.service=" +   
             f"{build_config.config.service_name}")

  ret.append(f"LABEL com.nvidia.omniverse.build.release={release}")
  ret.append(f"LABEL com.nvidia.omniverse.build.family={family}")
  ret.append(f"LABEL com.nvidia.omniverse.build.branch={branch}")
  ret.append(f"LABEL com.nvidia.omniverse.build.build={build}")

  ret.append(f"LABEL com.nvidia.omniverse.build.build_tool_version={VERSION}")

  return(ret)

def check_is_an_offending_label(line):
  offending_labels = [ 'com.nvidia.omniverse.service',
                       'com.nvidia.omniverse.build.release', 
                       'com.nvidia.omniverse.build.family', 
                       'com.nvidia.omniverse.build.version',
                       'com.nvidia.omniverse.build.build']

  for l in offending_labels:
    offending_substring = f"LABEL {l}"
    if(offending_substring in line):
      logging.error(f"    > {l} label found in your image config, please " + 
                    "remove it")

      logging.error(f"NOTE: yes, with this version of `build.py`, " + 
                     "you no longer need to have build-related labels " + 
                     "in your image config (Dockerfile). They will be "   + 
                     "added automatically.")

      logging.error(f"The following labels will cause this error: ")
      for _ in offending_labels:
        logging.error(f"  > {_}")

      die(f"Please remove them, and try again.")
      

def set_version(dest_path, version):
  with open(f"{dest_path}/VERSION", 'w') as vfh:
    vfh.write(version)

def get_cache_registry(image_config_path):
  if(args.cache_registry):
    logging.info(f"    > specified as {args.cache_registry}")
    return(args.cache_registry)
  else:
    logging.info(f"    > attempting to auto-detect") 
    image_config_dir = os.path.dirname(os.path.realpath(image_config_path))
    ret = nvidia.gitlab.utils.get_gitlab_registry_url(image_config_dir,     
                                                      log_prefix='    ')
    logging.info(f"    > {ret}")
    return(ret)


def parse_args():
  argparser = argparse.ArgumentParser(description=description)

  argparser.add_argument("configs", metavar="config", nargs='+', default=None,
                         help="Build configuration file")

  argparser.add_argument("-f", "--family", metavar="family",
                         default=defaults.family,
                         dest="family", 
                         help=f"Family for this image " + 
                              f"(default `{defaults.family}`)"
                        )

  argparser.add_argument("-no", "--build-number", metavar="number",
                         default=None,
                         dest="build_no", 
                         help=f"Build number (DO NOT USE EXCEPT IN CI!)"
                        )

  argparser.add_argument("-d", "--dry",
                          default=False, action='store_true',
                          dest="dry_run", 
                          help="Dry run (do not actually do anything)")

  argparser.add_argument("--damp",
                          default=False, action='store_true',
                          dest="damp_run", 
                          help="Damp run (will prep the build dir but won't build)")

  argparser.add_argument("-s", "--server", metavar="server",
                          default=None,
                          dest="server", 
                          help="Docker server to use (defaults to environment)")

  argparser.add_argument("--save",
                          default=False, action='store_true',
                          dest="save_image_file", 
                          help="Save image file (useful when you want a .tar of " +
                               "your build"
                        )

  argparser.add_argument("-o", "--outdir", metavar="dir",
                          default=os.getcwd(), 
                          dest="out_dir", 
                          help="Save image to dir (default CWD)"
                        )

  argparser.add_argument("--enforce-compliance", metavar="{1|0}",
                          default=0,
                          dest="enforce_compliance",
                          help="Enforce compliance with licensing and other "+ 
                               "requirements"
                        )

  argparser.add_argument("--report", 
                         default=0, 
                         action="store_true", 
                         dest="generate_report", 
                         help="Produce report on built images on " + 
                             f"STDOUT in JSON",
                        )

  argparser.add_argument("--dump-env", 
                         default=0, 
                         action="store_true", 
                         dest="dump_env", 
                         help="Dump environment before building (useful for " + 
                              "CI debug)"
                        )

  argparser.add_argument("--plain-progress", 
                         default=0,
                         action="store_true", 
                         dest="plain_progress", 
                         help="Use plain (not fancy) output for " +     
                              "Docker BuildKit")

  argparser.add_argument("--no-buildkit", 
                         default=0,
                         action="store_true", 
                         dest="no_buildkit", 
                         help="Do not use Docker BuildKit",)
         
  
  argparser.add_argument("--cache-registry",
                         default="",
                         metavar="url",
                         dest="cache_registry",
                         help="Path of the image registry to look for images " +
                              "to be used as cached layers and provided "+
                              "to `docker build` in --cache-from option. " + 
                              "Defaults to this project's Gitlab registry."
                         )

  argparser.add_argument("--cache-tag",
                         metavar="tag",
                         default=[],
                         nargs='+',
                         dest="cache_tags",
                         help="List of image tags to use as a cache for " + 
                              "builds (--cache-from <r>/<i>:tag_a " + 
                              "<r>/<i>:tag_b ...)"
                         )

  argparser.add_argument("-r", "--release", metavar="version",
                         #default=defaults.default_release,
                         default=None,
                         dest="release", 
                         help="DEPRECATED, DO NOT USE"
                        )

  argparser.add_argument("-b", "--build", metavar="build",
                         default=None, 
                         dest="build", 
                         help="DEPRECATED, DO NOT USE"
                        )

  argparser.add_argument("--ssh", 
                          default=False, action='store_true',
                          dest="ssh", 
                          help="Use SSH to connect to Docker"
                        )

  global args
  args = argparser.parse_args()

  configs_dict = { config: config for config in args.configs }

  if(len(configs_dict) != len(args.configs)):
    logging.error("Looks like you provided the same config path twice!")
    die("Please correct, and re-try")

  if(args.build):
    die("You have provided the `-b(uild)` argument, which" + 
        " is no longer supported. Please review " + 
        " README.md")

  if(args.release):
    die("You have provided the `-r(elease)` argument, which" + 
        " is no longer supported. Please review " + 
        " README.md")

  if(norm_string(args.family) != args.family):
    die(f"Invalid family: `{args.family}`")
  
  if(args.cache_registry and not args.cache_tags):
    die("Cannot use remote registry for cache without " + 
        "providing image tags")

  args.enforce_compliance = bool(int(args.enforce_compliance))

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

def get_outfile_path(service_name, tag):
  if not args.save_image_file:
    return(None) 
  
  filename = service_name + "-" + tag + ".tar"
  out_dir = os.path.realpath(args.out_dir)

  if not (os.path.exists(out_dir)):
    if not (args.dry_run):
      os.makedirs(out_dir)
  elif not (os.path.isdir(args.out_dir)):
    raise Exception(f"{args.out_dir} exists, but is not a dir: can't output there!")
    
  return f"{out_dir}/{filename}"

def get_build(build_config):

  logging.info("  > determining build name")
  hash = nvidia.git.get_git_hash_short(os.path.dirname(build_config.path))

  logging.info(f"    > git hash: `{hash}`")

  ret = ''

  if(args.build_no):
    logging.info(f"    > build # `{args.build_no}` provided")
    ret = '.'.join([args.build_no, hash])
  else:
    ret = hash

  logging.info(f"  > build: `{ret}`")
  return(ret)

def get_image_tag(release, family, build, branch):
  return(f"{release}_{branch}.{family}.{build}")

def copy_code(build_config, dest_dir):
  # Paths inside CONFIGS are RELATIVE to CONFIGS
  code_root = os.path.join(os.path.dirname(build_config.path),
                           build_config.config.root)
  code_root = os.path.realpath(code_root)

  for fileset in build_config.config.files:
    logging.info(f"    > copying {fileset['source']} to {fileset['dest']}")
    copy_files(code_root, os.path.join(dest_dir, fileset['dest']), 
                          src_subdir=fileset['source'],
                          src_files=fileset['files'])

def copy_files(src_dir, dest_dir, src_files=[], src_subdir=''):
  for source_file in src_files:
    dirname = os.path.dirname(source_file)
    dest = dest_dir

    logging.info(f"      > adding '{source_file}'")



    if(dirname):
      dest = os.path.join(dest, dirname)

    if(source_file.endswith('*')):
      shutil.copytree(os.path.join(src_dir, src_subdir, dirname), dest) 
    else:  
      (not os.path.exists(dest)) and os.makedirs(dest)
      shutil.copy2(os.path.join(src_dir, src_subdir, source_file), dest)

def get_dockerfile_func_args(func, release=None, family=None, build=None):
  all_args = { 'family' : family, 
               'version' : build, 
               'build' : build, 
               'release' : release }

  supported_args = func.__code__.co_varnames[:func.__code__.co_argcount]

  if(('family' in supported_args) and 
     ('release' not in supported_args)):
     return(dict(family="-".join([release,family]), version=build))
  elif not len(supported_args):
    return({})
  else:
    ret = dict( (x,all_args[x]) for x in supported_args )
    return(ret)

#def get_release(build_config):
#  logging.info("  > determining version (release) name")
#
#  version = load_project_version(build_config)
##  branch = get_branch(build_config)
#
#  ret = ''
#
#  if(version):
#    ret =  version #"-".join([version, branch])
#  else:
#    ret = defaults.no_version #branch
#
#  logging.info(f"  > version (release): `{ret}`")
#  return(ret)
#
#def get_branch(build_config):
#  logging.info("  > determining branch") 
#  path = os.path.dirname(build_config.path)
#  logging.info(f"  > using path: {path}")
#
#  branch = None
#
#  if(nvidia.gitlab.ci.is_ci_env()):
#    logging.info("    > looks like gitlab CI env, using " + 
#                 "CI branch name detection") 
#
#    branch = nvidia.gitlab.ci.get_branch_name(path)
#  else: 
#    logging.info("    > looks like regular env, using git branch name")
#    branch = nvidia.git.get_cur_branch(path)
#
#  logging.info(f"    > detected `{branch}`")
#  branch = norm_string(branch)
#  logging.info(f"    > normalized to `{branch}`")
#  return(branch)
#
#def norm_string(string):
#  string = re.sub("[^a-zA-Z0-9._-]", "-", string)
#  string = re.sub("-+", "-", string)
#  return(string)
#
#def load_project_version(build_config):
#  version_file_path =(f"{os.path.dirname(build_config.path)}/" + 
#                      f"{defaults.default_version_file}")
#
#  version_file_path = os.path.abspath(version_file_path)
#  logging.info(f"    > attempting to load from {version_file_path}")
#
#  if(not os.path.isfile(version_file_path)):
#    logging.info(f"    > not found")
#    return(None)
#
#  with open(version_file_path, 'r') as h:
#    version = h.read()
#
#  version = version.rstrip().lstrip()
#  logging.info(f"  > loaded release version `{version}`")
#  if not(len(version)):
#    die("Loaded emptry string, can't continue") 
#
#  return(version)

def get_dockerignore(build_config):
  ret = None

  if(hasattr(build_config.config, "ignore")):
    logging.info("  > processing .dockerignore")

    ret = ''

    for _ in build_config.config.ignore:
      logging.info(f"    > added {_}")
      ret += f"{_}\n"

  return(ret)

################################################################################
## Execute
################################################################################

init()
main()

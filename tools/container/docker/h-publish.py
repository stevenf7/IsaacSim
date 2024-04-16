#!/usr/bin/env python3.8

################################################################################
## Libs
################################################################################

import sys
import os 

bin_path = os.path.dirname(os.path.realpath(__file__))

sys.path.append(f"{bin_path}/lib")
sys.path.append(f"{bin_path}/common/lib")

import argparse

import logging

import shutil

from pprint import pprint

import nvidia.docker.registry.argparse

from nvidia.die import die
from nvidia.helm import Helm
from nvidia.helm.chart import Chart, is_chart_dir
from nvidia.sysutils import reset_dir

from nvidia.repo import find_repo_root

import nvidia.build.versioning
from nvidia.build.versioning import make_kube_compliant_version

################################################################################
## Globals
################################################################################

description = "HELM Chart publishing tool"
args = None

work_dir = f"{bin_path}/__helm_publish"

class defaults:
  family = 'local'
  no_version = 'no_version'
  default_release="private"
  default_version_file="../../../VERSION.md" # relative to HELM chart
  repo_root_rel="../../.." # relative to HELM chart

helm = None 

################################################################################
## Init
################################################################################

def init():
  nvidia.die.log_instead_of_stderr()

  logging.basicConfig(format="%(message)s", level=logging.INFO)

  global helm 
  helm = Helm()

  parse_args()
  if(not args.no_reset_work_dir):
    reset_dir(work_dir)

################################################################################
## Main
################################################################################

def main():
  if(not is_chart_dir(args.chart_path)):
    die(f"{args.chart_path} is not a Helm chart!")

  logging.info(f"Publishing chart: {args.chart_path}")
  logging.info(f"Destination:      {args.registry}")
  

  to_publish = get_versions_to_publish()
  registry = get_images_registry()

  for version_info in to_publish:
    v_f = version_info['version_full']
    a_v = version_info['app_version']
    v = version_info['version']
    t = version_info['images']

    logging.info(f"-"*79)
    logging.info(f"Publishing {v}")

    chart = Chart(path=args.chart_path)
    app_name = chart.app_name()
    chart = None

    chart_work_dir = os.path.join(work_dir, f'{app_name}-{v}')
    if(os.path.isdir(chart_work_dir)):
      shutil.rmtree(chart_work_dir)
    logging.info(f"Copying chart from {args.chart_path} to {chart_work_dir}")
    shutil.copytree(args.chart_path, chart_work_dir)

    chart = Chart(path=chart_work_dir)

    logging.info(f"  > setting chart version to `{v}`, app version `{a_v}`")
    chart.set_version(version=v, app_version=a_v )
    logging.info(f"  > setting chart's full version to `{v_f}`")
    chart.set_version_full(v_f)
    logging.info(f"  > setting chart's images tag to `{t}`")
    no_updated_values = chart.set_images_tag(t)
    logging.info(f"    > {no_updated_values} tags updated")
    logging.info(f"  > setting chart's image registry to `{registry}`")
    no_updated_values = chart.set_registry(registry)
    logging.info(f"    > {no_updated_values} entries updated")

    if(args.update_dependencies):
      logging.info("  > updating dependencies") 
      res = helm.update_deps(chart, user=args.user, pwd=args.password)
      if(res is None):
        logging.info("    > chart has no dependencies") 
      else:
        logging.info(f"    > updated {res} dependencies") 
        

    logging.info("  > linting")
    if(not helm.lint(chart)):
      die("  > linting failed, can't proceed!")

      
    if(not args.dry_run):
      logging.info("  > publishing")
      helm.publish_chart(chart, target_reg=args.registry, 
                                user=args.user, 
                                pwd=args.password)

    
################################################################################
## Functions
################################################################################

def get_images_registry():
  logging.info("Determining which image registry to use")

  if(args.image_registry):
    logging.info(f"  > image registry provided:  {args.image_registry}")
    return(args.image_registry)

  if(args.registry_by_type):
    if(reg := args.registry_by_type.get('docker', None)):
      logging.info(f"  > automatically using:  {reg}")
      return(reg)

  die("Can't find corresponding docker image registry associated with " + 
     f"{args.registry}. Please provide one on the command line.")
     

def get_versions_to_publish():
  logging.info("Determining versions to publish") 
  logging.info("-"*79) 

  
  logging.info("searching for repo root") 
  repo_root = find_repo_root(os.path.abspath(args.chart_path))
  logging.info(f"  > repo root: {repo_root}")

  release = nvidia.build.versioning.get_release(repo_root)
  branch = nvidia.build.versioning.get_branch(repo_root)
  build = nvidia.build.versioning.get_build(repo_root, build_no=args.build_no)

  version_full = nvidia.build.versioning.get_version_full(release=release,    
                                                          family=args.family, 
                                                          build=build, 
                                                          branch=branch)

  images_tag = nvidia.build.versioning.get_docker_image_tag(release=release,    
                                                           family=args.family, 
                                                           build=build, 
                                                           branch=branch)

  images_tag = args.images_tag if args.images_tag else images_tag 

  logging.info("-"*79) 
  logging.info(f"Version (full): {version_full}")
  logging.info(f"Images tag    : {images_tag}")

  ret = [ { 'version' : version_full, 
            'app_version': make_kube_compliant_version(version_full),
            'version_full': version_full, 
            'images': images_tag
          }
        ]

  for v in args.extra_versions:
    tag = args.images_tag if args.images_tag else v
    logging.info(f"+ adding extra version to publish: `{v}`, " + 
                 f"images tag `{tag}`")
    av = make_kube_compliant_version(v)
    ret.append({ 'version': v, 
                 'app_version': av,
                 'version_full': version_full, 'images': tag })
  logging.info("-"*79) 

  return(ret)

def parse_args():
  argparser = argparse.ArgumentParser(description=description)

  argparser.add_argument("chart_path", metavar="path", default=None,
                         help="Chart location")

  argparser.add_argument("-f", "--family", metavar="family",
                         default=defaults.family,
                         dest="family", 
                         help=f"Family for this chart, used in version " +      
                               "construction " + 
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
                          help=("Dry run (prepare, but do not publish " + 
                               "the chart)")
                        )

  argparser.add_argument("-v", "-t", "--version", "--tag",
                          action='append',
                          metavar="<version>",
                          default=[],
                          dest="extra_versions", 
                          help="Publish using these additional versions",
                        )

  argparser.add_argument("-ir", "--image-registry", metavar="registry",
                         default=None,
                         dest="image_registry", 
                         help=f"Image registry to use (by default, will " +
                              f"attempt to construct image registry to be "  + 
                              f"the same as the chart registry"
                        )

  argparser.add_argument("-it", "--image-tag", metavar="tag",
                         default=None,
                         dest="images_tag", 
                         help=f"Images tag (by default, will " +
                              f"use chart's version as images tag)"  
                        )

  argparser.add_argument("-u", "--user", metavar="username",
                         default='$oauthtoken',
                         dest="user", 
                         required=0,
                         help=f"Username (login) for registry, default "
                              f"$oauthtoken " + 
                              f"(can also use OMNI_HP_USER)"
                        )

  argparser.add_argument("-p", "--password", metavar="password",
                         default=None,
                         dest="password", 
                         required=0,
                         help=f"Password for registry " + 
                              f"(can also use OMNI_HP_PASSWORD)"
                        )

  argparser.add_argument("--update-dependencies",
                          default=False, action='store_true',
                          dest="update_dependencies", 
                          help="Update chart's dependencies"
                        )

  argparser.add_argument("--no-reset-wd",
                          default=False, action='store_true',
                          dest="no_reset_work_dir", 
                          help="Don't reset working directory",
                        )


  nvidia.docker.registry.argparse.add_registry_args(argparser, "registry", 
                                                    type="helm")

  global args
  args = argparser.parse_args()

  err = nvidia.docker.registry.argparse.parse_registry_args(args, "registry", 
                                                            type="helm", 
                                   registry_by_type_target="registry_by_type")

  if(err):
    die(err)
    sys.exit(1)

  if(not args.registry):
    logging.error("You did not provide target registry.")
    logging.error("Please review available options with `--help` arg, " +   
                  "and make a pick.") 
    die()

  if(not args.user):
    args.user = os.getenv('OMNI_HP_USER', None)

  if(not args.password):
    args.password = os.getenv('OMNI_HP_PASSWORD', None)


################################################################################
## Execute
################################################################################

init()
main()




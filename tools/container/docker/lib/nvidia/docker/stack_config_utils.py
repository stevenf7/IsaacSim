#!/usr/bin/python3.6 

import os
import sys
from pprint import pprint 
import logging
import re
import yaml

this_dir = os.path.abspath(os.path.dirname(__file__))

def add_promtail(compose, docker_conn = None, 
                 loki_server = None, state_dir = None,
                 deploy_opts = {}, stack_name = None,
                 common_labels = {}, logs = [],):
  assert(compose)
  assert(docker_conn)
  assert(len(state_dir))
  assert(len(stack_name))
  assert(len(loki_server))
  assert(len(logs))

  # TODO can add argument to override promtail version, if necessayr
  # TODO not doing that right now - want to see if one version across
  # TODO the board will work out. -- Fidot, Nov 13'19

  promtail_image = "grafana/promtail:v0.4.0"

  logging.info(f"  > Adding Promtail image and configuration to your stack") 
  download_image(docker_conn, image=promtail_image)

  loki_server = loki_server.rstrip("/")
  if(loki_server.startswith("http://")):
    logging.warning(f"   > note: you added http:// to your loki server. " +     
                     "I'll handle that, but please don't do it")
    loki_server = loki_server.lstrip("http://")

  loki_url = f"http://{loki_server}/api/prom/push"
  logging.info(f"  > Loki URL: {loki_url}")
  (scrape_config, paths_to_mount) = _get_log_scrape_config(
                                        job_name = stack_name,
                                        common_labels = common_labels,    
                                        logs = logs)
  scrape_config_file = f"{deploy_opts['_work_dir']}/promtail.yml"     
  logging.info(f"  > writing Promtail config to {scrape_config_file}")
  with open(scrape_config_file, 'w') as h:
    h.write(scrape_config)

  service_config = yaml.load(f"""
                              image: "{promtail_image}"
                              deploy:
                                replicas: 1
                                restart_policy:
                                  condition: on-failure
                              configs: 
                                - source: promtail_config
                                  target: /etc/promtail/promtail.yml
                              command: 
                                - -config.file 
                                - /etc/promtail/promtail.yml
                                - -client.url
                                - http://{loki_server}/api/prom/push
#                                - -log.level
#                                -  debug
                                - -positions.file
                                - /omni/loki_state/positions.yaml
#                              entrypoint: /bin/bash -c
#                              command: ["sleep 1000000"]
                              environment: 
                              volumes:
                             """)

  service_config['environment'] = []
  service_config['volumes'] = []

  for (h,c) in paths_to_mount.items():
    service_config['volumes'].append(f"{h}:{c}")

  service_config['volumes'].append(f"{state_dir}:/omni/loki_state")

  compose_ds = yaml.load(compose)
  compose_ds['services']['promtail'] = service_config

  if('configs' not in compose_ds):
    compose_ds['configs'] = {}

  compose_ds['configs']['promtail_config'] = { 'file': scrape_config_file }
  return(yaml.dump(compose_ds, default_flow_style=0))

def download_image(docker, image=None):
  assert(image) 
  logging.info(f"     > downloading {image}")
  return(docker.api.images.pull(image))

def split_host_port_opt(opt_name, opt):
  split = opt.split(":")
  if(len(split) != 2):
    logging.error(f"'{opt_name}' option value corrupt: should be host:port")
    logging.error(f"You provided: {opt}")
    sys.exit(1)

  (host, port) = split

  if(not port.isdigit()):
    logging.error(f"{opt_name}: port value is not numeric.")
    logging.error("Option value should be host:port")
    logging.error(f"You provided: {opt}")
    sys.exit(1)

  return(host,port)

################################################################################
## Private
################################################################################

def _get_log_scrape_config(common_labels, logs, job_name):
  scrape_configs = []
  mount_no = 1
  mount_map = {}
  kinds = {}

  required_labels = ['omni_service', 'omni_instance',]

  logging.info(f"  > Configuring logs")

  for log in logs:
    host_root = log['host_root']
    logging.info(f"    > log file: {log['file_subpath']}")
    logging.info(f"      > host root: {log['host_root']}")
    if(host_root not in mount_map):
      mount_map[host_root] = "/omni/logs/" + str(mount_no)
      logging.info(f"    > will be at {mount_map[host_root]} in the container")
      mount_no += 1

    if(log['kind'] in kinds):
      logging.info(f"  > Seems like {log['kind']} shows up at least twice " + 
                   f"in the config provided - can't continue")
      sys.exit()
    else:
      kinds[log['kind']] = 1

    log_container_path = f"{mount_map[host_root]}/{log['file_subpath']}"
    config = yaml.load(f"""
                        job_name: {job_name}-{log['kind']}
                        static_configs:
                        - targets: ['localhost']
                          labels:
                            omni_log_kind: {log['kind']}
                            __path__: {log_container_path}
                          """)
    labels = config['static_configs'][0]['labels']
    labels.update(common_labels)
    if('labels' in log):
      for l in log['labels']:
        labels[l] = log['labels'][l]

    for l in required_labels:
      if l not in labels:
        logging.error(f"    > Label `{l}` required, but not present")
        sys.exit(1)

    scrape_configs.append(config) 

  ret = {'scrape_configs': [] }
  ret['scrape_configs'] = scrape_configs 

  return(yaml.dump(ret, default_flow_style=0), mount_map)

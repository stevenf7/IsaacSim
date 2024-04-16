import sys
import os
import subprocess
import re

from urllib.parse import urlparse, urlunparse

from nvidia.sysutils import push_dir_pos, pop_dir_pos

from nvidia.die import die

from pprint import pprint

def is_git_repo_path(path):
  push_dir_pos(path)

  nullfd = os.open(os.devnull, os.O_RDWR)
  ret = subprocess.call(['git', 'status'], stdout=nullfd, stderr=nullfd)
  os.close(nullfd)

  pop_dir_pos()

  return(not ret)

def get_git_hash_short(path):
  return(_run_git_cmd_ret_stdout(path, ['git', 'rev-parse', '--short=8', 'HEAD']))

def get_origin_url(path):
  ret = _run_git_cmd_ret_stdout(path, ['git', 'config', '--get', 'remote.origin.url'])
  return(_sanitize_url(ret))


def get_cur_branch(path):
  return(_run_git_cmd_ret_stdout(path,
                                 ['git', 'rev-parse', '--abbrev-ref', 'HEAD']))

def bundle(repo_path, out_file=None, branch='master'):
  assert(out_file) 

  if(os.path.isfile(out_file)):
    die("Can't create `{out_file}`: already present") 

  _run_git_cmd(['bundle', 'create', out_file, branch], repo_path=repo_path)

def clone(repo, root_path):
  _run_git_cmd(['clone', repo], repo_path=root_path)

def set_user(repo_path, user='', email=''):
  assert(len(user))
  assert(len(email))

  _run_git_cmd(['config', 'user.name', user], repo_path=repo_path)
  _run_git_cmd(['config', 'user.email', email], repo_path=repo_path)

def pull(repo_path): _run_git_cmd(['pull'], repo_path=repo_path)
def fetch(repo_path): _run_git_cmd(['fetch'], repo_path=repo_path)

def initmods(repo_path): 
  _run_git_cmd(['submodule', 'update', '--init', '--recursive'], 
               repo_path=repo_path)

def push(repo_path):
  _run_git_cmd(['push', '--set-upstream', 'origin', get_cur_branch(repo_path)], 
               repo_path=repo_path
              )

def init_repo(repo_path):

   if(os.path.exists(repo_path)):
     die(f"{repo_path} already exists") 

   os.makedirs(repo_path)
   _run_git_cmd(['init'], repo_path=repo_path)
   _run_git_cmd(['commit', '--allow-empty', '-m', 'First commit'],
                 repo_path=repo_path)

def commit(repo_path, message=''):
  assert(len(message))
  _run_git_cmd(['add', '-A'], repo_path=repo_path)
  _run_git_cmd(['commit', '-m', message], repo_path=repo_path)

def checkout(repo_path, branch, make_new=0): 
  cmd = ['checkout']
  if(make_new):
    cmd.append('-b')
  cmd.append(branch)

  _run_git_cmd(cmd, repo_path=repo_path)

def merge(repo_path, branch=''):
  assert(len(branch))

  cmd = ['merge']
  cmd.append(branch)

  _run_git_cmd(cmd, repo_path=repo_path)

def _run_git_cmd(args, repo_path=None, fail_ok=0):

  if(repo_path):
    push_dir_pos(repo_path)

  cmd = ['git'] + args
  ret = subprocess.call(cmd)

  if(repo_path):
    pop_dir_pos()

  if(ret and not fail_ok):
    die(f"{' '.join(cmd)} failed with {ret}")


def _run_git_cmd_ret_stdout(path, cmd):
  push_dir_pos(path)
  ret = subprocess.run(cmd, stdout=subprocess.PIPE)
  pop_dir_pos()

  if(ret.returncode):
    raise Exception(f"Failed to run {cmd}: maybe not a GIT repo?")

  return(ret.stdout.decode('utf-8').strip())

def _sanitize_url(url):

  url = 'https://gitlab-ci-token:64_6wKzyfqnrj262wkcNMaj@gitlab-master.nvidia.com/omniverse/docker'
  parsed = urlparse(url, allow_fragments=1)
  netloc = re.sub("^.*@", "", parsed.netloc)
  ret = urlunparse([parsed.scheme,
                    netloc, 
                    parsed.path, 
                    parsed.params,
                    parsed.query,
                    parsed.fragment])
  return(ret)

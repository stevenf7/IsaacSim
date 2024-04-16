
def err_out(*args):
  import sys

  for i in args:
    sys.stderr.write(i)

  sys.stderr.flush()

def login(user='', prompt='Login', *args, **kwargs):
  import getpass


  err_out(f"{prompt} [{user}]: ")
  login = input()
  if(not len(login)):
    login = user

  pwd = getpass.getpass()

  return((login, pwd))


   


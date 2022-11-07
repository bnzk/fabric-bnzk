import os
import sys

import environ
from fabric.api import task, run, roles, cd, execute, hide, puts, env
from fabric.context_managers import settings
from fabric.contrib.console import confirm
from fabric.operations import local, put
from fabric.contrib.project import rsync_project

from .database import put_db, get_db, create_db, create_local_db  # noqa


# hm. https://github.com/fabric/fabric/issues/256
sys.path.insert(0, sys.path[0])

# set some basic things, that are just needed.
env.forward_agent = True


from fabric_bnzk.bootstrap import (
    bootstrap, create_virtualenv, create_nginx_folders, create_supervisor_folders, clone_repos
)
from fabric_bnzk.database import (
    create_db, create_local_db, create_mycnf, get_db, put_db
)

__all__ = [
    'bootstrap',
    'create_virtualenv',
    'create_nginx_folders',
    'create_supervisor_folders',
    'clone_repos',
    'create_db',
    'create_local_db',
    'create_mycnf',
    'get_db',
    'put_db',
    # 'get_db_mysql',
    # 'put_db_mysql',
    # 'get_db_postgresql',
    # 'put_db_postgresql',

]

# check for some defaults to be set?
# in a method, to be called after each setup? ie at the end of stage/live?
# def check_setup():
#     if not getattr(env, 'project_name'):
#         exit("env.project_name must be set!")
# project_name
# repository
# sites
# is_postgresql
# is_nginx_gunicorn
# needs_main_nginx_files
# is_uwsgi
# remote_ref
# requirements_files
# requirements_file
# is_python3
# deploy_crontab
# roledefs
# project_dir = '/home/{main_user}/sites/{project_name}-{env_prefix}'.format(**env)
# virtualenv_dir = '{project_dir}/virtualenv'.format(**env)
# gunicorn_restart_command = '~/init/{site_name}.{env_prefix}.sh restart'
# nginx_restart_command = '~/init/nginx.sh restart'
# uwsgi_restart_command = 'touch $HOME/uwsgi.d/{site_name}.{env_prefix}.ini'
# project_conf = 'project.settings._{project_name}_{env_prefix}'.format(**env)

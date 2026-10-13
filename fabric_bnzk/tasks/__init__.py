import sys

from fabric.api import env

from fabric_bnzk.tasks.bootstrap import (
    bootstrap,
    clone_repos,
    create_custom_python,
    create_virtualenv,
)
from fabric_bnzk.tasks.database import (
    create_db,
    create_local_db,
    create_mycnf,
    get_db,
    put_db,
)
from fabric_bnzk.tasks.glitchtip import setup_all_glitchtip_alerts, setup_glitchtip
from fabric_bnzk.tasks.gunicorn import (
    copy_restart_gunicorn,
    disable_gunicorn,
    stop_gunicorn,
)
from fabric_bnzk.tasks.helper_tasks import (
    dj,
    fix_permissions,
    get_media,
    memory,
    put_media,
    shell,
    version,
    virtualenv,
)
from fabric_bnzk.tasks.local import pip_compile, pip_init_upgrade
from fabric_bnzk.tasks.main_tasks import (
    build_put_webpack,
    collectstatic,
    crontab,
    deploy,
    disable_django,
    git_set_remote,
    migrate,
    put_env_file,
    requirements,
    restart,
    stop_django,
    update,
)
from fabric_bnzk.tasks.nginx import copy_restart_nginx, create_nginx_folders
from fabric_bnzk.tasks.supervisor import (
    copy_restart_supervisord,
    create_supervisor_folders,
    supervisorctl,
)
from fabric_bnzk.tasks.uwsgi import copy_restart_uwsgi

# hm. https://github.com/fabric/fabric/issues/256
sys.path.insert(0, sys.path[0])

# set some basic things, that are just needed.
env.forward_agent = True


__all__ = [
    "bootstrap",
    "pip_init_upgrade",
    "pip_compile",
    "create_virtualenv",
    "create_custom_python",
    "create_nginx_folders",
    "create_supervisor_folders",
    "clone_repos",
    "create_db",
    "create_local_db",
    "create_mycnf",
    "deploy",
    "update",
    "restart",
    "put_env_file",
    "build_put_webpack",
    "stop_django",
    "disable_django",
    "crontab",
    "migrate",
    "requirements",
    "collectstatic",
    "git_set_remote",
    "get_db",
    "put_db",
    "copy_restart_gunicorn",
    "stop_gunicorn",
    "disable_gunicorn",
    "dj",
    "version",
    "shell",
    "memory",
    "get_media",
    "put_media",
    "virtualenv",
    "fix_permissions",
    "create_nginx_folders",
    "copy_restart_nginx",
    "create_supervisor_folders",
    "supervisorctl",
    "copy_restart_supervisord",
    "copy_restart_uwsgi",
    "setup_glitchtip",
    "setup_all_glitchtip_alerts",
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

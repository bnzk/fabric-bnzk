import datetime
import os

from fabric.api import task, run, settings, roles, hide, env
from fabric.contrib.console import confirm
from fabric.operations import get, local, put
from fabric.utils import puts


@task
@roles('web', 'db')
def create_nginx_folders():
    """
    do it.
    """
    if getattr(env, 'needs_main_nginx_files', None):
        with hide('running', 'stdout'):
            exists = run('if [ -d "~/nginx" ]; then echo 1; fi')
        if exists:
            puts('nginx dir already exists. manual action needed, if really...')
            return
        run('mkdir ~/nginx')
        run('mkdir ~/nginx/conf')
        run('mkdir ~/nginx/conf/sites')
        run('mkdir ~/nginx/temp')
        run('mkdir ~/nginx/logs')
        run('mkdir ~/nginx/logs/archive')
        puts('created ~/nginx & co.'.format(**env))
    else:
        puts('no nginx files created, check "needs_main_nginx_files" in env.')


def copy_restart_nginx():
    for site in env.sites:
        run(
            'cp {project_dir}/deployment/nginx/{site}-{env_prefix}.txt'
            ' $HOME/nginx/conf/sites/.'.format(site=site, **env)
        )
    # nginx main, may be optional!
    if env.needs_main_nginx_files:
        run('cp {project_dir}/deployment/nginx/logrotate.conf'
            ' $HOME/nginx/conf/.'.format(**env))
        run('cp {project_dir}/deployment/nginx/nginx.conf'
            ' $HOME/nginx/conf/.'.format(**env))
        if not getattr(env, 'is_supervisord', None):
            run('cp {project_dir}/deployment/nginx/nginx.sh $HOME/init/.'.format(**env))
            run('chmod u+x $HOME/init/nginx.sh')
    if not getattr(env, 'is_supervisord', None):
        run(env.nginx_restart_command)
    else:
        run('cp {project_dir}/deployment/supervisor/programs/nginx'
            ' $HOME/supervisor/programs/.'.format(**env))

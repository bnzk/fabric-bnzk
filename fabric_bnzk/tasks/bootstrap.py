import datetime
import os

from fabric.api import task, run, settings, roles, hide, env
from fabric.contrib.console import confirm
from fabric.operations import get, local, put
from fabric.utils import puts

from fabric_bnzk.tasks.nginx import create_nginx_folders
from fabric_bnzk.tasks.supervisor import create_supervisor_folders
from fabric_bnzk.tasks.database import create_db


@task
@roles('web', 'db')
def bootstrap():
    clone_repos()
    create_nginx_folders()
    create_supervisor_folders()
    create_virtualenv()
    create_db()
    puts('Bootstrapped {project_name} on {host} (cloned repos, created venv and db).'.format(**env))


@task
@roles('web', )
def create_virtualenv(force=False):
    """
    Bootstrap the environment.
    """
    with hide('running', 'stdout'):
        exists = run('if [ -d "{virtualenv_dir}" ]; then echo 1; fi'.format(**env))
    if exists:
        if not force:
            puts('Assuming virtualenv {virtualenv_dir} has already been created '
                 'since this directory exists.'
                 'If you need, you can force a recreation.'.format(**env))
            return
        else:
            run('rm -rf {virtualenv_dir}'.format(**env))
    venv_command = 'virtualenv {virtualenv_dir} '.format(**env)
    if getattr(env, 'is_python3', None):
        venv_command += ' --python=python3'
    run(venv_command)
    requirements()
    puts('Created virtualenv at {virtualenv_dir}.'.format(**env))


@task
@roles('web', 'db')
def clone_repos():
    """
    clone the repository.
    """
    with hide('running', 'stdout'):
        exists = run('if [ -d "{project_dir}" ]; then echo 1; fi'.format(**env))
    if exists:
        puts('Assuming {repository} has already been cloned since '
             '{project_dir} exists.'.format(**env))
        return
    run('git clone {repository} {project_dir}'.format(**env))
    puts('cloned {repository} to {project_dir}.'.format(**env))


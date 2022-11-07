import datetime
import os

from fabric.api import task, run, settings, roles, hide, env
from fabric.contrib.console import confirm
from fabric.operations import get, local, put
from fabric.utils import puts


@task
@roles('web', 'db')
def create_supervisor_folders():
    if getattr(env, 'is_supervisord', None):
        run('mkdir --parents ~/supervisor/programs')
        run('mkdir --parents ~/supervisor/logs')


@task
@roles('web')
def copy_restart_supervisord():
    """
    install and restart supervisord
    """
    if env.get('is_supervisord', None):
        run('mkdir --parents ~/supervisor/programs')
        run('mkdir --parents ~/supervisor/logs')
        run(
            'cp {project_dir}/deployment/supervisor/supervisord.conf'
            ' ~/supervisor/.'.format(**env)
        )
        run(
            'cp {project_dir}/deployment/supervisor/supervisord.sh'
            ' ~/init/.'.format(**env)
        )
        run('chmod u+x $HOME/init/supervisord.sh')

        # programs
        run('rm -f ~/supervisor/programs/*-{env_prefix}'.format(**env))
        run(
            'cp {project_dir}/deployment/supervisor/programs/*-{env_prefix}'
            ' ~/supervisor/programs/.'.format(**env)
        )

        # restart
        run('~/init/supervisord.sh restart')
        # run('supervisorctl -c ~/supervisor/supervisord.conf update')
        run('supervisorctl -c ~/supervisor/supervisord.conf status')
    else:
        puts('not deploying supervisord to %s!' % env.env_prefix)


@task
@roles('web')
def supervisorctl(command):
    """
    control supervisord
    """
    if env.get('is_supervisord', None):
        run('supervisorctl -c ~/supervisor/supervisord.conf {}'.format(command))
    else:
        puts('supervisord not deployed to %s!' % env.env_prefix)

import datetime
import os

from fabric.api import task, run, settings, roles, hide, env
from fabric.contrib.console import confirm
from fabric.operations import get, local, put
from fabric.utils import puts


def copy_restart_uwsgi():
    for site in env.sites:
        run(
            'cp {project_dir}/deployment/uwsgi/{site}-{env_prefix}.ini'
            ' $HOME/uwsgi.d/.'.format(site=site, **env)
        )
        # cp does the touch already!
        # run(env.uwsgi_restart_command.format(site=site, **env))

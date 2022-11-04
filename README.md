# fabric tasks for typical bnzk deployments

[![CI](https://img.shields.io/github/workflow/status/bnzk/fabric-bnzk/CI.svg?style=flat-square&logo=github "CI")](https://github.com/bnzk/fabric-bnzk/actions/workflows/ci.yml)


Using fabric ([fab-classic](https://github.com/ploxiln/fab-classic)) and ansible-vault (for encryption of .env files)

There are mainly two hosting providers covered:

- djangoeurope.com, using supervisord or init files for gunicorn and nginx
- nine.ch, using nginx, uwsgi (emperor mode)

Automatic put/get for mysql/postrgres and for media files is implemented

Future development could involve using djangoeurope API and nine.ch's sudo tools to allow even
more of the bootstrapping process to be automated.

## Usage

Create a fabfile and import tasks:

```python
# fabfile.py:

from fabric.api import task, env

from fabric_bnzk.main_tasks import *  # noqa

# ==============================================================================
# main env definition
# ==============================================================================
env.is_python3 = True
env.project_name = 'your_project_name'  # name of git repos?
env.repository = 'git@bitbucket.org:bnzk/{project_name}.git'.format(**env)
env.sites = ('{{ project_name }}',)
env.is_postgresql = True  # False for mysql! only used for put/get_db
env.needs_main_nginx_files = True
env.is_supervisord = True
env.is_nginx_gunicorn = True
env.is_uwsgi = False
env.is_apache = False
env.remote_ref = 'origin/main'
# these will be checked for changes
env.requirements_files = [
    'requirements/deploy.txt',
    'requirements/deploy.in',
    'requirements/basic.in',
]
# this is used with pip install -r
env.requirements_file = env.requirements_files[0]


# ==============================================================================
# tasks which set up deployment environments
# ==============================================================================

@task
def live():
    """
    Use the live deployment environment.
    """
    env.env_prefix = 'live'
    env.deploy_crontab = True
    env.main_user = '{project_name}'.format(**env)
    server = '{main_user}@s20.wservices.ch'.format(**env)
    env.roledefs = {
        'web': [server],
        'db': [server],
    }
    generic_env_settings()


@task
def stage():
    """
    Use the sandbox deployment environment on xy.bnzk.ch.
    """
    env.env_prefix = 'stage'
    env.deploy_crontab = False
    env.main_user = 'bnzk-stage'.format(**env)
    server = '{main_user}@s20.wservices.ch'.format(**env)
    env.roledefs = {
        'web': [server],
        'db': [server],
    }
    generic_env_settings()


def generic_env_settings():
    if not getattr(env, 'deploy_crontab', None):
        env.deploy_crontab = False
    env.project_dir = '/home/{main_user}/sites/{project_name}-{env_prefix}'.format(**env)
    env.virtualenv_dir = '{project_dir}/virtualenv'.format(**env)
    env.gunicorn_restart_command = '~/init/{site}-{env_prefix}.sh restart'
    env.gunicorn_stop_command = '~/init/{site}-{env_prefix}.sh stop'
    env.nginx_restart_command = '~/init/nginx.sh restart'
    # not needed with uwsgi emporer mode, cp is enough
    # env.uwsgi_restart_command = 'touch $HOME/uwsgi.d/{site}-{env_prefix}.ini'
    env.project_conf = 'project.settings._{project_name}_{env_prefix}'.format(**env)


stage()


```

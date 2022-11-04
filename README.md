# fabric tasks for typical bnzk deployments

Using fabric ([fab-classic](https://github.com/ploxiln/fab-classic)) and ansible-vault (for encryption of .env files).
Works best with [bnzk/django-layout](https://github.com/bnzk/django-layout) - this repos contains many of the
expected files (nginx configs, supervisord, init files, etc) that are needed for deployment.

There are mainly two hosting providers covered:

- djangoeurope.com, using supervisord or init files for gunicorn and nginx
- nine.ch, using nginx, uwsgi (emperor mode)

Automatic put/get for mysql/postrgres and for media files is implemented

Future development could involve using djangoeurope API and nine.ch's sudo tools to allow even
more of the bootstrapping process to be automated.


## Basic Setup

Create a fabfile and import tasks:

```python
# fabfile.py:
from fabric_bnzk import *  # noqa

env.project_name = 'your_project_name'  # required. used to create folder name on server
env.repository = 'git@bitbucket.org:organization/{project_name}.git'.format(**env)  # required. repos? 
env.remote_ref = 'origin/main'  # required. remote branch to be checked out and deployed
env.project_conf = 'project.settings'  # required
env.env_prefix = ''  # default: ''. env prefix, used to build repos folder name: projectname-env_prefix.
  # Can be empty if you dont have multiple envs, or if they are on different servers/user accounts
env.main_user = '{project_name}'.format(**env)  # required. user to login to the server
server = '{main_user}@s20.wservices.ch'.format(**env)  # required. user@server.com ssh connection string
env.roledefs = {  # deprecated but required for now. future versions will only support one server!
    'web': [server],
    'db': [server],
}

env.build_put_webpack = True  # default: True. build and put the frontend assets during deploy? not needed if you
  # have your assets in version control, or if your assets are built within django/libsass/etc.
env.is_python3 = True  # default: True. legacy setting ;-)
env.sites = ('{{ project_name }}', 'another_site', )  # default: (env.project_name, ). django sites
  # (from sites framework) to be run
env.is_postgresql = True  # default: True. False for mysql. only used for put/get_db/create_db
env.needs_main_nginx_files = True  # default: True. False if you have more than one project under one user on the server (not recomended)
env.is_supervisord = True  # default: True. use supervisord to run gunicorn/nginx (djangoeurope mode)
env.is_nginx_gunicorn = True  # default: True. run nginx/gunicorn (djangoeurope mode)
env.is_uwsgi = False  # default: False. run with uwsgi (nine.ch mode)
env.is_apache = False  # default: False. not supported ;-)
env.deploy_crontab = True  # default: True. deploy the crontab?

# these will be checked for changes
env.requirements_files = [
    'requirements/deploy.txt',
    'requirements/deploy.in',
    'requirements/basic.in',
]
# this is used with pip install -r
env.requirements_file = env.requirements_files[0]

# these are optional, but are "constructed" if empty (as below), or customized, if needed
env.project_dir = '/home/{main_user}/sites/{project_name}'.format(**env)  # optional
if env.env_prefix:
    env.project_dir += '-{env_prefix}'.format(**env)
env.virtualenv_dir = '{project_dir}/virtualenv'.format(**env)  # optional

env.gunicorn_restart_command = '~/init/{site}-{env_prefix}.sh restart'  # optional 
env.gunicorn_stop_command = '~/init/{site}-{env_prefix}.sh stop'  # optional
env.nginx_restart_command = '~/init/nginx.sh restart'  # optional


```


## Usage

Once setup, you can use the built in tasks. For example:

```bash
$ fab show # (instead of "show", enter any other not existing task) to get a list of available commands
$ fab bootstrap  # bootstrap on remote server: clone_repos, create_virtualenv and install libs, create_db, 
  # copy nginx initial files 
$ fab deploy  # deploy: update, collectstatic, migrate, deploy crontab, restart
$ fab update  # update repos (and dependencies in virtualenv) only
$ fab shell:'ps fux'  # check server processes
$ fab dj:createsuperuser  # execute django management command
$ fab memory  # memory consumption
$ fab restart  # restart only
$ fab get_db get_media  # fetch db and media files
```

## Advanced Setup

Use fabric tasks seperate between stage and live environment. The one and very important thing: All changes that you
apply on the `env` in one "environment switch" must be applied in the other switche(s) too. Otherwise you'll end up with
an inconsistent `env`. 

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


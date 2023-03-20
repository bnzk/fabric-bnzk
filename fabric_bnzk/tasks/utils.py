import environ
from fabric.operations import local
from fabric.state import env
from fabric.contrib import django


def get_settings(conf=None):
    # do this here. django settings cannot be imported more than once...probably.
    # still dont really get the mess here.
    if not conf:
        conf = env.project_conf
    django.settings_module(conf)
    from django.conf import settings
    return settings


def load_local_env_vars():
    environ.Env.read_env('.env', overwrite=True)


def load_remote_env_vars():
    local("ansible-vault decrypt {env_file} --output .env-temp".format(**env))
    environ.Env.read_env('.env-temp', overwrite=True)
    local('rm .env-temp')

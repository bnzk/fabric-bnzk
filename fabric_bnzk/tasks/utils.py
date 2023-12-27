from importlib import reload

from fabric.operations import local
from fabric.state import env
from fabric.contrib import django


def get_settings(conf=None):
    # do this here. django settings cannot be imported more than once...probably.
    # still dont really get the mess here.
    # TADA: https://stackoverflow.com/questions/437589/how-do-i-unload-reload-a-python-module
    if not conf:
        conf = env.project_conf
    django.settings_module(conf)
    from django import conf
    reload(conf)
    return conf.settings


def load_local_env_vars():
    import environ
    environ.Env.read_env('.env', overwrite=True)


def load_remote_env_vars():
    import environ
    local("ansible-vault decrypt {env_file} --output .env-temp".format(**env))
    environ.Env.read_env('.env-temp', overwrite=True)
    local('rm .env-temp')

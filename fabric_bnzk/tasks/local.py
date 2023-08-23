from fabric.api import env, task, local


@task
def pip_init_upgrade():
    local('pip install --upgrade pip setuptools wheel pip-tools')


@task
def pip_compile(upgrade=False):
    flags = ''
    flags += ' --upgrade ' if upgrade else ''
    flags += ' --generate-hashes ' if env.pip_compile_hashes else ''
    local(f'pip-compile requirements/dev.in {flags}')
    local('pip-sync requirements/dev.txt')
    local(f'pip-compile requirements/deploy.in {flags}')
    local('pip-audit')

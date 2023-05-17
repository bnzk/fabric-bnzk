from fabric.api import task, local


@task
def pip_init():
    local('pip install --upgrade pip setuptools wheel pip-tools')


@task
def pip_compile(upgrade=False):
    flag = '--upgrade' if upgrade else ''
    local(f'pip-compile requirements/dev.in {flag}')
    local('pip-sync requirements/dev.txt')
    local(f'pip-compile requirements/deploy.in {flag}')
    local('pip-audit')



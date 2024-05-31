from fabric.api import task, run, roles, hide, env, cd
from fabric.utils import puts

from fabric_bnzk.tasks.database import create_db
from fabric_bnzk.tasks.main_tasks import requirements
from fabric_bnzk.tasks.helper_tasks import virtualenv
from fabric_bnzk.tasks.nginx import create_nginx_folders
from fabric_bnzk.tasks.supervisor import create_supervisor_folders


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
def create_custom_python(force=False):
    if getattr(env, 'custom_python3', None):
        # custom python!
        with hide('running', 'stdout'):
            exists = run('if [ -d "$HOME/python{custom_python3}" ]; then echo 1; fi'.format(**env))
        if exists:
            if not force:
                puts('Custom ~/python{custom_python3} folder has already been created'.format(**env))
                return
            else:
                run('rm -rf python{custom_python3}'.format(**env))
            run('wget https://www.python.org/ftp/python/{custom_python3}/Python-{custom_python3}.tar.xz'.format(**env))
            run('tar -xJf Python-{custom_python3}.tar.xz'.format(**env))
            run('rm Python-{custom_python3}.tar.xz'.format(**env))
            with cd('Python-{custom_python3}'.format(**env)):
                run('./configure --prefix $HOME/python{custom_python3} && make && make install'.format(**env))
            run('rm -rf Python-{custom_python3}'.format(**env))


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
    if getattr(env, 'custom_python3', None):
        # custom python!
        venv_command = '~/python{custom_python3}/bin/python3 -m venv {virtualenv_dir}'.format(**env)
    else:
        # system python
        venv_command = 'virtualenv {virtualenv_dir} '.format(**env)
        if getattr(env, 'is_python3', None):
            venv_command += ' --python=python3'
    run(venv_command)
    virtualenv("pip install -U pip setuptools wheel")
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

from .database import create_db


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


@task
@roles('web', 'db')
def create_nginx_folders():
    """
    do it.
    """
    if getattr(env, 'needs_main_nginx_files', None):
        with hide('running', 'stdout'):
            exists = run('if [ -d "~/nginx" ]; then echo 1; fi')
        if exists:
            puts('nginx dir already exists. manual action needed, if really...')
            return
        run('mkdir ~/nginx')
        run('mkdir ~/nginx/conf')
        run('mkdir ~/nginx/conf/sites')
        run('mkdir ~/nginx/temp')
        run('mkdir ~/nginx/logs')
        run('mkdir ~/nginx/logs/archive')
        puts('created ~/nginx & co.'.format(**env))
    else:
        puts('no nginx files created, check "needs_main_nginx_files" in env.')

import os

from fabric.api import cd, task, run, roles, hide, env, execute
from fabric.contrib.console import confirm
from fabric.operations import local, put
from fabric.utils import puts

from fabric_bnzk.tasks import copy_restart_gunicorn, copy_restart_uwsgi, stop_gunicorn, disable_gunicorn
from fabric_bnzk.tasks.helper_tasks import dj
from fabric_bnzk.tasks.nginx import copy_restart_nginx
from fabric_bnzk.tasks.supervisor import copy_restart_supervisord
from fabric_bnzk.tasks.helper_tasks import virtualenv


@task
def deploy(verbosity='noisy'):
    """
    Full server deploy.r
    Updates the repository (server-side), synchronizes the database, collects
    static files and then restarts the web service.
    """
    if verbosity == 'noisy':
        hide_args = []
    else:
        hide_args = ['running', 'stdout']
    with hide(*hide_args):
        puts('Updating repository...')
        execute(update)
        puts('Build put webpack...')
        execute(build_put_webpack)
        puts('Putting encrypted env file')
        execute(put_env_file)
        puts('Collecting static files...')
        execute(collectstatic)
        puts('Synchronizing database...')
        execute(migrate)
        puts('Restarting everything...')
        execute(restart)
        puts('Installing crontab...')
        execute(crontab)


@task
@roles('web')
def git_set_remote():
    """
    reset the repository's remote.
    """
    with cd(env.project_dir):
        remote, dest_branch = env.remote_ref.split('/', 1)
        run('git remote remove {}'.format(remote))
        run('git remote add {} {}'.format(remote, env.repository))
        run('git fetch {}'.format(remote))
        run('git branch --set-upstream-to={} {}'.format(env.remote_ref, dest_branch))


@task
@roles('web', 'db')
def update(action='check', tag=None):
    """
    Update the repository (server-side).

    By default, if the requirements file changed in the repository then the
    requirements will be updated. Use ``action='force'`` to force
    updating requirements. Anything else other than ``'check'`` will avoid
    updating requirements at all.
    """
    with cd(env.project_dir):
        remote, dest_branch = env.remote_ref.split('/', 1)
        run('git fetch {remote}'.format(remote=remote,
                                        dest_branch=dest_branch, **env))
        with hide('running', 'stdout'):
            changed_files = run('git diff-index --cached --name-only '
                                '{remote_ref}'.format(**env)).splitlines()
        if not changed_files and action != 'force':
            # No changes, we can exit now.
            return
        reqs_changed = False
        if action == 'check':
            for file in env.requirements_files:
                if file in changed_files:
                    reqs_changed = True
                    break
        # before. run('git merge {remote_ref}'.format(**env))
        if tag:
            run('git checkout tags/{tag}'.format(tag=tag, **env))
        else:
            run('git checkout {dest_branch}'.format(dest_branch=dest_branch, **env))
            run('git pull'.format(dest_branch=dest_branch, **env))
        run('find -name "*.pyc" -delete')
        run('git clean -df')
        # run('git clean -df {project_name} docs requirements public/static '.format(**env))
        # fix_permissions()
    if action == 'force' or reqs_changed:
        # Not using execute() because we don't want to run multiple times for
        # each role (since this task gets run per role).
        requirements()


@task
@roles('web')
def crontab():
    """
    install crontab
    """
    if env.deploy_crontab:
        if getattr(env, 'contab_file', None):
            crontab_file = env.crontab_file
        else:
            crontab_file = 'deployment/crontab.txt'
        with cd(env.project_dir):
            run('crontab {}'.format(crontab_file))
    else:
        puts('not deploying crontab to %s!' % env.env_prefix)


@task
@roles('web')
def collectstatic():
    """
    Collect static files from apps and other locations in a single location.
    """
    dj('collectstatic --link --noinput')


@task
@roles('db')
def migrate():
    """
    migrate the database.
    """
    dj('migrate --noinput')


@task
@roles('web')
def restart():
    """
    Copy gunicorn & nginx config, restart them.
    """
    if env.is_nginx_gunicorn:
        if not getattr(env, 'is_supervisord', None):
            copy_restart_gunicorn()
        copy_restart_nginx()
    if env.is_uwsgi:
        copy_restart_uwsgi()
    if env.is_apache:
        exit("apache restart not implemented!")
    if env.get('is_supervisord', None):
        copy_restart_supervisord()
    if env.get('is_systemd', None):
        exit("global systemd restart not implemented!")


@task
@roles('web')
def stop_django():
    """
    stop django, for now, may be restarted...beware
    """
    if env.is_nginx_gunicorn:
        stop_gunicorn()
    if env.is_uwsgi:
        exit("uswgi stop not implemented!")
        # stop_uwsgi()
    if env.is_apache:
        exit("apache stop not implemented!")


@task
@roles('web')
def disable_django():
    """
    disable django service/app completely
    """
    if env.is_nginx_gunicorn:
        disable_gunicorn()
    if env.is_uwsgi:
        exit("uswgi disable not implemented!")
        # disable_uwsgi()
    if env.is_apache:
        exit("apache disable not implemented!")


@task
@roles('web', 'db')
def requirements():
    """
    Update the requirements.
    """
    # let it get some more older
    # virtualenv('pip-sync {project_dir}/{requirements_file}'.format(**env))
    virtualenv('pip install -r {project_dir}/{requirements_file}'.format(**env))


@task
@roles('web')
def build_put_webpack():
    """
    build webpack, put on server!
    env attributes:
    - webpack_build_command, defaults to npm run build
    - webpack_bundle_path, defaults to 'apps/{project_name}/static/{project_name}/bundle'
    """
    if not env.get('is_webpack', False):
        return
    local_branch = local('git branch --show-current')
    if not env.remote_ref.endswith(local_branch):
        yes_no = confirm("Configured remote_ref for {} is {}, but you are on branch {}. Continue anyway (y/N)?", default=False)
        if not yes_no:
            exit(0)
    local(env.get('webpack_build_command', 'npm run build'))
    execute(put_webpack_bundle)


@task
@roles('web')
def put_webpack_bundle():
    base_static_path = 'apps/{project_name}/static/{project_name}/bundle'.format(**env)
    base_static_path = env.get('webpack_bundle_path', base_static_path)
    local_path = base_static_path + '/*'
    remote_path = '{}/{}'.format(env.project_dir, base_static_path)
    run('mkdir --parents {}'.format(remote_path))
    put(local_path=local_path, remote_path=remote_path)


@task
def put_env_file():
    """
    put the ansible-vault encrypted env file, with ansible, so it will be decrypted
    """
    if getattr(env, 'env_file', None):
        values = {
            'server': env.roledefs['web'][0],
            'locale_path': env.env_file,
            'remote_path': env.get('remote_env_file', os.path.join(env.project_dir, '.env')),
            'user': env.main_user,
        }
        local('ansible {server} --inventory {server}, '
              '--module-name ansible.builtin.copy '
              '--user {user} '
              '--args "src={locale_path} dest={remote_path}"'
              ''.format(**values))

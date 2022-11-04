

# ==============================================================================
# Actual tasks
# ==============================================================================


@task
def deploy(verbosity='noisy'):
    """
    Full server deploy.
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
        puts('Putting encrypted env file')
        execute(put_env_file)
        puts('Collecting static files...')
        execute(collectstatic)
        puts('Synchronizing database...')
        execute(migrate)
        puts('Restarting web server...')
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
        stop_uwsgi()
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
        disable_uwsgi()
    if env.is_apache:
        exit("apache disable not implemented!")





def copy_restart_uwsgi():
    for site in env.sites:
        run(
            'cp {project_dir}/deployment/uwsgi/{site}-{env_prefix}.ini'
            ' $HOME/uwsgi.d/.'.format(site=site, **env)
        )
        # cp does the touch already!
        # run(env.uwsgi_restart_command.format(site=site, **env))


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
def get_version():
    """
    Get installed version from each server.
    """
    with cd(env.project_dir):
        run('git describe --tags')
        run('git log --graph --pretty=oneline -n20')


@task
@roles('web')
def get_media():
    """
    get media files. path by convention, adapt if needed.
    """
    # trivial version
    # get(os.path.join(env.project_dir, 'public', 'media'), 'public/media')
    if getattr(env, 'custom_media_root', None):
        remote_dir = env.custom_media_root
        if remote_dir[-1] == '/':
            # cannot end with a slash! rsync is not working!
            remote_dir = remote_dir[0:-1]
    else:
        remote_dir = os.path.join(env.project_dir, 'public', 'media', )
    local_dir = os.path.join('public')
    extra_opts = ""
    # extra_opts = "--dry-run"
    rsync_project(
        remote_dir=remote_dir,
        local_dir=local_dir,
        upload=False,
        delete=True,
        extra_opts=extra_opts,
    )


@task
@roles('web')
def put_media():
    """
    put media files. path by convention, adapt if needed.
    """
    yes_no1 = confirm(
        "Will overwrite your remote media files! Continue?",
        default=False,
    )
    if not yes_no1:
        return
    yes_no2 = confirm("Are you sure?", default=False)
    if not yes_no2:
        return

    # go for it!
    if getattr(env, 'custom_media_root', None):
        cust = env.custom_media_root
        remote_dir, to_remove = os.path.split(env.custom_media_root)
        if not to_remove:
            # custom media root ended with a slash - let's do it again!
            remote_dir, to_remove = os.path.split(cust)
    else:
        remote_dir = os.path.join(env.project_dir, 'public', )
    local_dir = os.path.join('public', 'media')
    extra_opts = ""
    # extra_opts = "--dry-run"
    rsync_project(
        remote_dir=remote_dir,
        local_dir=local_dir,
        upload=True,
        delete=True,
        extra_opts=extra_opts,
    )


# ==============================================================================
# Helper functions
# ==============================================================================

def virtualenv(command):
    """
    Run a command in the virtualenv. This prefixes the command with the source
    command.
    Usage:
        virtualenv('pip install django')
    """
    source = 'source {virtualenv_dir}/bin/activate && '.format(**env)
    run(source + command)


@task
@roles('web')
def dj(command):
    """
    Run a Django manage.py command on the server.
    """
    cmd_prefix = 'cd {project_dir}'.format(**env)
    if getattr(env, 'custom_manage_py_root', None):
        cmd_prefix = 'cd {}'.format(env.custom_manage_py_root)
    virtualenv(
        '{cmd_prefix} && export DJANGO_SETTINGS_MODULE={project_conf} && ./manage.py {dj_command}'.format(
            dj_command=command,
            cmd_prefix=cmd_prefix,
            **env
        )
    )


@task
@roles('web')
def shell(command):
    """
    Run an arbitrary command on the server.
    """
    run(command)


@task
@roles('web')
def memory():
    """
    Run an arbitrary command on the server.
    """
    run("ps -U %s --no-headers -o rss | awk '{ sum+=$1} END {print int(sum/1024) \"MB\"}'" % (env.main_user))


def fix_permissions(path='.'):
    """
    Fix the file permissions. what a hack.
    """
    puts("no need for fixing permissions yet!")
    return

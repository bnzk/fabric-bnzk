

@task
@roles('web')
def version():
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

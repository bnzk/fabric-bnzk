import datetime
import os

import environ
from fabric.api import task, run, settings, roles, hide, env
from fabric.contrib.console import confirm
from fabric.operations import get, local, put
from fabric.utils import puts

from .utils import get_settings, load_remote_env_vars


@task
@roles('db')
def create_local_db():
    # this will fail straight if the database already exists.
    if env.is_postgresql:
        puts('PostgreSQL db must be created manually.')
    else:
        run("echo \"copye paste if this is not working!\"")
        run("echo \"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            "\" | mysql --user=root".format(
                db_name=_get_local_db_name(),
            )
        )


@task
@roles('db')
def create_db():
    # this will fail straight if the database already exists.
    if env.is_postgresql:
        puts('PostgreSQL db must be created manually.')
    else:
        options, db_name, prompts = _get_mysql_options_name_prompts()
        with settings(prompts=prompts):
            run("echo \"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                "\" | mysql {options} ".format(
                    db_name=db_name,
                    options=options,
                )
            )


@task
@roles('db')
def get_db(dump_only=False):
    local_db_name = _get_local_db_name()
    if env.is_postgresql:
        get_db_postgresql(local_db_name, dump_only)
    else:
        get_db_mysql(local_db_name, dump_only)


@task
@roles('db')
def put_db(local_db_name=False, from_file=None):
    yes_no1 = confirm(
        "This will erase your remote DB! Continue?",
        default=False,
    )
    if not yes_no1:
        return
    yes_no2 = confirm("Are you sure?", default=False)
    if not yes_no2:
        return

    if not local_db_name:
        local_db_name = _get_local_db_name()
    # go for it!
    if env.is_postgresql:
        put_db_postgresql(local_db_name, from_file)
    else:
        put_db_mysql(local_db_name, from_file)


def _get_mysql_options_name_prompts():
    options = ''
    host, port, name, user, password = _get_db_credentials()
    prompts = {}
    if host:
        options += ' --host={}'.format(host)
    if port:
        options += ' --port={}'.format(port)
    if user:
        options += ' --user={}'.format(user)
    if password:
        options += ' --password'
        prompts = {
            'Enter Password: ': password,
            'Enter password: ': password,
            'Enter password for user {}: '.format(user): password,
            'Enter Password for user {}: '.format(user): password,
        }
    return options, name, prompts


def get_db_mysql(local_db_name, dump_only=False):
    """
    dump db on server, import to local mysql (must exist)
    """
    date = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    dump_name = 'dump_%s_%s-%s.sql' % (env.project_name, env.env_prefix, date)
    remote_dump_file = os.path.join(env.project_dir, dump_name)
    local_dump_file = './%s' % dump_name
    options, db_name, prompts = _get_mysql_options_name_prompts()
    with settings(prompts=prompts):
        run('mysqldump '
            '{options} '
            ' {database} > {file}'.format(
                options=options,
                # cnf_file=my_cnf_file,
                database=getattr(env, 'remote_db_name', db_name),
                file=remote_dump_file,
            )
        )
    get(remote_path=remote_dump_file, local_path=local_dump_file)
    run('rm %s' % remote_dump_file)
    if not dump_only:
        local('mysql -u root %s < %s' % (local_db_name, local_dump_file))
        local('rm %s' % local_dump_file)


def put_db_mysql(local_db_name, from_file):
    """
    dump local db, import on server database (must exist)
    """
    if not from_file:
        dump_name = 'dump_for_%s.sql' % env.env_prefix
        local_dump_file = './%s' % dump_name
        local('mysqldump --user=root {database} > {file}'.format(
            database=local_db_name,
            file=local_dump_file,
        ))
    else:
        dump_name = os.path.basename(from_file)
        local_dump_file = from_file
    remote_dump_file = os.path.join(env.project_dir, dump_name)
    put(remote_path=remote_dump_file, local_path=local_dump_file)
    if not from_file:
        local('rm %s' % local_dump_file)
    options, db_name, prompts = _get_mysql_options_name_prompts()
    with settings(prompts=prompts):
        run('mysql '
            '{options} '
            # no more' --defaults-file={cnf_file}'
            ' {database} < {file} '.format(
                options=options,
                # cnf_file=my_cnf_file,
                database=env.get('remote_db_name', db_name),
                file=remote_dump_file,
                **env
            )
        )
    run('rm %s' % remote_dump_file)


@task
@roles('db')
def create_mycnf(force=False):
    my_cnf_file = _get_my_cnf_name()
    with hide('running', 'stdout'):
        exists = run('if [ -f "{cnf_file}" ]; then echo 1; fi'.format(cnf_file=my_cnf_file, **env))
    if force or not exists:
        settings = get_settings()
        db_settings = settings.DATABASES
        if exists:
            run('rm {cnf_file}'.format(cnf_file=my_cnf_file, **env))
        local('echo "[client]" >> {cnf_file}'.format(cnf_file=my_cnf_file, **env))
        local('echo "# The following password will be sent to all'
              'standard MySQL clients" >> {cnf_file}'.format(cnf_file=my_cnf_file, **env))
        local('echo "password = \"{pw}\"" >> {cnf_file}'.format(
                cnf_file=my_cnf_file,
                pw=db_settings["default"]["PASSWORD"],
                **env
            )
        )
        local('echo "user = \"{db_user}\"" >> {cnf_file}'.format(
                cnf_file=my_cnf_file,
                db_user=db_settings["default"]["USER"],
                **env
            )
        )
        put('{cnf_file}'.format(cnf_file=my_cnf_file))
        local('rm {cnf_file}'.format(cnf_file=my_cnf_file, **env))


def _get_postgres_options_name_prompts():
    options = ''
    host, port, name, user, password = _get_db_credentials()
    prompts = {}
    if host:
        options += ' --host={}'.format(host)
    if port:
        options += ' --port={}'.format(port)
    if user:
        options += ' --username={}'.format(user)
    if password:
        options += ' --password'
        prompts = {
            'Password: ': password,
            'Password for user {}: '.format(user): password,
        }
    return options, name, prompts


def get_db_postgresql(local_db_name, remote_db_name, dump_only=False):
    """
    dump db on server, import to local mysql (must exist)
    """
    date = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    dump_name = 'dump_%s_%s-%s.sql' % (env.project_name, env.env_prefix, date)
    remote_dump_file = os.path.join(env.project_dir, dump_name)
    local_dump_file = './%s' % dump_name
    options, db_name, prompts = _get_postgres_options_name_prompts()
    with settings(prompts=prompts):
        run('pg_dump {options} --clean --no-owner --if-exists --schema=public {database} > {file}'.format(
            options=options,
            database=getattr(env, 'remote_db_name', db_name),
            file=remote_dump_file,
        ))
    get(remote_path=remote_dump_file, local_path=local_dump_file)
    run('rm %s' % remote_dump_file)
    if not dump_only:
        # local('dropdb %s_dev' % env.project_name)
        # local('createdb %s_dev' % env.project_name)
        local('psql %s < %s' % (local_db_name, local_dump_file))
        local('rm %s' % local_dump_file)


def put_db_postgresql(local_db_name, from_file):
    """
    dump local db, import on server database (must exist)
    """
    if not from_file:
        dump_name = 'dump_for_%s.sql' % env.env_prefix
        local_dump_file = './%s' % dump_name
        local('pg_dump --clean --no-owner --if-exists --schema=public {database} > {file}'.format(
            database=local_db_name,
            file=local_dump_file,
        ))
    else:
        dump_name = os.path.basename(from_file)
        local_dump_file = from_file
    remote_dump_file = os.path.join(env.project_dir, dump_name)
    put(remote_path=remote_dump_file, local_path=local_dump_file)
    if not from_file:
        local('rm %s' % local_dump_file)
    # up you go
    options, name, prompts = _get_postgres_options_name_prompts()
    with settings(prompts=prompts):
        run('psql {options} {database} < {file}'.format(
            options=options,
            database=name,
            file=remote_dump_file,
        ))
    run('rm %s' % remote_dump_file)


def _get_my_cnf_name():
    return '.{project_name}-{env_prefix}.cnf'.format(**env)


def _get_local_db_name():
    local_db_name = getattr(env, 'local_db_name', None)
    if not local_db_name:
        local_db_name = env.project_name
    return local_db_name


def _get_remote_db_name():
    remote_db_name = getattr(env, 'remote_db_name', None)
    if not remote_db_name:
        if env.env_file:
            host, port, name, user, password = _get_db_credentials()
            remote_db_name = name
        else:
            django_settings = get_settings()
            remote_db_settings = django_settings.DATABASES.get('default', None)
            remote_db_name = remote_db_settings.get('NAME', '')
    return remote_db_name


def _get_db_credentials():
    if env.env_file:
        load_remote_env_vars()
        to_get_from = os.environ
        get_prefix = 'DB_'
        if os.environ.get('DATABASE_URL', ''):
            get_prefix = ''
            e = environ.Env()
            to_get_from = e.db_url()
        host = to_get_from.get(get_prefix + 'HOST', '')
        port = to_get_from.get(get_prefix + 'PORT', '')
        name = to_get_from.get(get_prefix + 'NAME', '')
        user = to_get_from.get(get_prefix + 'USER', '')
        password = to_get_from.get(get_prefix + 'PASSWORD', '')
    else:
        django_settings = get_settings()
        remote_db_settings = django_settings.DATABASES.get('default', None)
        host = remote_db_settings.get('HOST', '')
        port = remote_db_settings.get('PORT', '')
        name = remote_db_settings.get('NAME', '')
        user = remote_db_settings.get('USER', '')
        password = remote_db_settings.get('PASSWORD', '')
    return host, port, name, user, password
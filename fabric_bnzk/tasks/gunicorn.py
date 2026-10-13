from fabric.api import run, env


def disable_gunicorn():
    stop_gunicorn()
    for site in env.sites:
        run('rm $HOME/init/{site}-{env_prefix}.sh'.format(site=site, **env))


def stop_gunicorn():
    for site in env.sites:
        run(env.gunicorn_stop_command.format(site=site, **env))


def copy_restart_gunicorn():
    for site in env.sites:
        run(
            'cp {project_dir}/deployment/gunicorn/{site}-{env_prefix}.sh'
            ' $HOME/init/.'.format(site=site, **env)
        )
        run('chmod u+x $HOME/init/{site}-{env_prefix}.sh'.format(site=site, **env))
        if (not env.get('is_supervisord', None) and not env.get('is_systemd', None)):
            # no pty: the SIGHUP sent when a pty session closes kills the
            # daemonized gunicorn before it has set up its signal handlers
            run(env.gunicorn_restart_command.format(site=site, **env), pty=False)

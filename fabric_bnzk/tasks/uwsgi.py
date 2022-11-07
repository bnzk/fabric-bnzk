


def copy_restart_uwsgi():
    for site in env.sites:
        run(
            'cp {project_dir}/deployment/uwsgi/{site}-{env_prefix}.ini'
            ' $HOME/uwsgi.d/.'.format(site=site, **env)
        )
        # cp does the touch already!
        # run(env.uwsgi_restart_command.format(site=site, **env))

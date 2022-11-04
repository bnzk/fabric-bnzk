

def copy_restart_nginx():
    for site in env.sites:
        run(
            'cp {project_dir}/deployment/nginx/{site}-{env_prefix}.txt'
            ' $HOME/nginx/conf/sites/.'.format(site=site, **env)
        )
    # nginx main, may be optional!
    if env.needs_main_nginx_files:
        run('cp {project_dir}/deployment/nginx/logrotate.conf'
            ' $HOME/nginx/conf/.'.format(**env))
        run('cp {project_dir}/deployment/nginx/nginx.conf'
            ' $HOME/nginx/conf/.'.format(**env))
        if not getattr(env, 'is_supervisord', None):
            run('cp {project_dir}/deployment/nginx/nginx.sh $HOME/init/.'.format(**env))
            run('chmod u+x $HOME/init/nginx.sh')
    if not getattr(env, 'is_supervisord', None):
        run(env.nginx_restart_command)
    else:
        run('cp {project_dir}/deployment/supervisor/programs/nginx'
            ' $HOME/supervisor/programs/.'.format(**env))

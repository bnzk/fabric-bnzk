

@task
def put_env_file():
    """
    put the ansible-vault encrypted env file, with ansible, so it will be decrypted
    """
    if getattr(env, 'env_file', None):
        values = {
            'server': env.roledefs['web'][0],
            'locale_path': env.env_file,
            'remote_path': os.path.join(env.project_dir, '.env'),
            'user': env.main_user,
        }
        local('ansible {server} --inventory {server}, '
              '--module-name ansible.builtin.copy '
              '--user {user} '
              '--args "src={locale_path} dest={remote_path}"'
              ''.format(**values))


@task
@roles('web')
def build_put_webpack():
    """
    build webpack, put on server!
    env attributes:
    - webpack_build_command, defaults to yarn build
    - webpack_bundle_path, defaults to 'apps/{project_name}/static/{project_name}/bundle'
    """
    local_branch = local('git branch --show-current')
    if not env.remote_ref.endswith(local_branch):
        yes_no = confirm("Configured remote_ref for {} is {}, but you are on branch {}. Continue anyway (y/N)?", default=False)
        if not yes_no:
            exit(0)
    local(env.get('webpack_build_command', 'yarn build'))
    base_static_path = 'apps/{project_name}/static/{project_name}/bundle'.format(**env)
    base_static_path = env.get('webpack_bundle_path', base_static_path)
    local_path = base_static_path + '/*'
    remote_path = '{}/{}'.format(env.project_dir, base_static_path)
    run('mkdir --parents {}'.format(remote_path))
    put(local_path=local_path, remote_path=remote_path)

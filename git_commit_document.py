from github import Github, GithubException

DEFAULT_BASE_URL = 'https://api.github.com'
DEFAULT_REPO_NAME = 'Visualize'
DEFAULT_BRANCH_NAME = 'using_git_plugin'


def operation_to_perform(target_repo, file_location, branch=DEFAULT_BRANCH_NAME):
    try:
        response = target_repo.get_contents(file_location, ref=branch)
        return response, response.sha
    except GithubException as exception:
        print exception.status
        print("==Creating the file in the repo as it doesn't exist...")
        response = target_repo.create_file(path=file_location,
                                           message="Dummy service arch is file is created",
                                           content="dummy",
                                           branch=branch
                                           )
        response = target_repo.get_contents(file_location, ref=branch)
        return response, response.sha


def commit_file_to_repo(username, access_token, file_location, branch=DEFAULT_BRANCH_NAME,
                        repo=DEFAULT_REPO_NAME):
    print('==Loggin in to github using oauth')
    git = Github(base_url=DEFAULT_BASE_URL,
                 login_or_token=access_token,
                 per_page=100)
    print('==Getting user: %s' % username)
    user = git.get_user(login=username)

    print('==Getting the target repo %s' % repo)
    target_repo = user.get_repo(repo)

    print('==checking if file exists..')
    file_pointer, sha = operation_to_perform(target_repo, file_location, branch)

    document_to_put = open(file_location, 'r').read()
    if sha is not None:
        print('==Updating the file as it already exists...')
        print str(target_repo.update_file(path=file_pointer.path,
                                          message="service_arch is update with new arch diagram..",
                                          content=document_to_put,
                                          sha=sha,
                                          branch=branch))
    else:
        print ('==Either the folder meta/ is not created in the repo. \n'
               '  Or The repo is not reachable.')

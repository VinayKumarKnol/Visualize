from github import Github

DEFAULT_BASE_URL = 'https://api.github.com'
DEFAULT_REPO_NAME = 'Visualize'
DEFAULT_BRANCH_NAME = 'using_git_plugin'


def operation_to_perfrom(target_repo, file_location, branch=DEFAULT_BRANCH_NAME):
    response = target_repo.get_contents(file_location, ref=branch)
    if response.size / 100 is not 0:
        return response, response.sha
    else:
        return response, None


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
    file_pointer, sha = operation_to_perfrom(target_repo, file_location, branch)

    document_to_put = open(file_location, 'r').read()
    print target_repo+file_pointer.path
    if sha is not None:
        print('==Updating the file as it already exists...')
        target_repo.update_file(path=file_pointer.path,
                                message="service_arch is update with new arch diagram..",
                                content=document_to_put,
                                sha=sha,
                                branch=branch)
    else:
        print("=Creating the file in the repo as it doesn't exist...")
        target_repo.create_file(path=file_location,
                                message="service_arch is being created for this branch.",
                                content=document_to_put,
                                branch=branch)

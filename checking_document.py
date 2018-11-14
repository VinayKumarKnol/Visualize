from string import Template
import requests
import json
from base64 import b64encode, b64decode
import defaults_env


def authenticate_user(username, client_id, client_secret):
    auth_url = defaults_env.oauth_url.substitute(username=username,
                                                 client_id=client_id,
                                                 client_secret=client_secret)
    print json.loads(requests.get(url=auth_url).content)


def encode_file_before_commit(location_of_file):
    with open(location_of_file, 'r') as service_png:
        return b64encode(service_png.read()).decode('utf-8')


def is_file_in_repo(username, repo, file_location, branch):
    repo_url = defaults_env.repo_content_url.substitute(
        username=username,
        repo=repo,
        path=file_location,
        branch=branch
    )
    print repo_url
    return requests.get(repo_url).ok


def retrieve_sha_of_file(username, repo, file_location, branch):
    if is_file_in_repo(username, repo, file_location, branch):
        repo_url = defaults_env.repo_content_url.substitute(
            username=username,
            repo=repo,
            path=file_location,
            branch=branch
        )
        response = json.loads(requests.get(repo_url).content)
        return response['sha']


def commit_file_to_repo(username, client_id, client_secret, repo, file_location, branch):
    authenticate_user(username, client_id, client_secret)
    repo_commit_url = defaults_env.repo_commit_url.substitute(
        username=username,
        repo=repo,
        path=file_location
    )
    commit_meta_data = ""
    if is_file_in_repo(username, repo, file_location, branch) is True:
        commit_meta_data = defaults_env.update_file_template. \
            substitute(commit_message="Updated the service architecture for this app group...",
                       base64_content=encode_file_before_commit(file_location),
                       username=username,
                       email="vinay.kumar@knoldus.in",
                       branch=branch,
                       sha_of_file=retrieve_sha_of_file(username, repo, file_location, branch))
    else:
        commit_meta_data = defaults_env.new_file_template. \
            substitute(commit_message="created the service architecture for this app group...",
                       base64_content=encode_file_before_commit(file_location),
                       username=username,
                       email="vinay.kumar@knoldus.in",
                       branch=branch
                       )
    # print commit_meta_data
    response = requests.put(repo_commit_url, data=commit_meta_data)
    # print response.content
    if response.ok is True:
        print "Repo %s is updated with %s  @ %s" % (repo, file_location, branch)
    else:
        print "There were some errors while committing this file, you may not have permission."

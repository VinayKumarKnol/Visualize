from string import Template

root_url = "https://api.github.com"
oauth_url = \
    Template(root_url + "/users/$username?client_id=$client_id&client_secret=$client_secret")
repo_content_url = Template(root_url + "/repos/$username/$repo/contents/$path?ref=$branch")
repo_commit_url = Template(root_url + "/repos/$username/$repo/contents/$path")
new_file_template = Template('''
{
  "message": $commit_message,
  "content" : $base64_content,
  "committer": {
    "name": $username,
    "email": $email
  },
  "branch" : $branch
}
''')
update_file_template = Template('''
{
  "message": $commit_message,
  "content" : $base64_content,
  "committer": {
    "name": $username,
    "email": $email
  },
  "branch" : $branch
  "sha": $sha_of_file
}
''')

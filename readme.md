**Visualizing of services deployed on a cluster**

Usage
```
 python draw_service_interaction.py  \
-cu <username>  \
-cp <password>
-u Saturn \
-s nginx-beta-infosight
-gu VinayKumarKnol \ 
-gr Visualize \ 
-gb using_git_plugin \ 
-gt <access_token>
```

Requirements:
1. DCOS CLI installed.
2. Credentials required to log-in to the cluster.
3. Github access token to commit to a repo.
4. GraphViz python library.

The script depends on the DCOS CLI. It works by first logging into the cluster by credentials.  
Then, it pulls the `service.json` which is stored under the `conf` folder. The script explores the `env` section of the
service json in order to co-relate any two services.

**Credentials Required**  
1. _Github Access Token_

In order to commit to the repo we require access token of the user running the script.
The access token is used with option `-gt` / `--git_access_token`

2. _User id to login to Cluster_
We require the login email which is used to login to the cluster. This is login email is specified with option
`-cu` / `--cluster_user_id` followed by the password specified by `-cp`  / `--cluster_user_password`



**Cluster Name**   
Given by the option `-u` / `--dcos_cluster_name`.  
Before we go to visualize through the script. We first need link the cluster to cli. 
Which can be done through the following command:  
```dcos cluster setup <dcos_url>```  
Then we should check that we are able to connect to the cluster. We'll have to keep note of the name of the cluster  
we're using.

**Starting point**  
Given by the option `-s` / `--starting_point`   
This is the point where from where the script will start the visualization from. Currently, the script only works if the  
the starting point is nginx.

**Github Related details**

In order to commit the data to a repo, the script has a function which will commit the 
`service_arch.png` under the `meta` folder to a repo of your choice under the path `meta/`

For this to work we need to specify the following options:
1. ```-gu``` / ```--git_username```: the github username of the user.
2. `--gr`/ `--git_repo`: the repository the user has the right to commit to.
3. `--gb` / `--git_branch`: the branch of the repository on which the user wants to make the commit.

 _Make sure you have the rights to add to the repo & Access token's scope includes the right to write to the repo._
 
After the script is successfully run we will have the output as `service_arc.png` which will have the diagram of the 
service made. We can find diagram under the ``meta`` folder.


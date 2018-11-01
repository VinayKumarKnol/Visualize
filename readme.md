**Visualizing of services deployed on a cluster**

Usage
```
 python draw_service_interaction.py  \
-c credentials.json \
-u Saturn \
-s nginx-beta-infosight
```

Requirements:
1. DCOS CLI installed.
2. Credentials required to log-in to the cluster
   must be stored in a json format.
3. GraphViz python library.

The script depends on the DCOS CLI. It works by first logging into the cluster by credentials.  
Then, it pulls the `service.json` which is stored under the `conf` folder. The script explores the `env` section of the
service json in order to co-relate any two services.

**Credentials Format**  
Credentials are specified the option `-c`.   
We should keep our login credentials in the following format:  
```
{
  "login":  {  
    "username": "your.username",
    "password": "your.password"
  }
}
 ```
 
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


After the script is successfully run we will have the output as `service_arc.png` which will have the diagram of the 
service made. We can find diagram under the ``meta`` folder.


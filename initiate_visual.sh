#!/bin/sh
dcos_cluster_name=Jupiter
username=sahil.sawhney@hpe.com
password=KnoldusTemp5555

dcos cluster attach $dcos_cluster_name
dcos auth login --username=$username --password=$password
dcos marathon app list --json

python draw_service_interaction.py -c credentials.json -u jupiter  
    

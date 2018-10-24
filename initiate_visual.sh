#!/bin/sh

source ./conf/_environment

echo "Trying to attach to $dcos_cluster_name.."
dcos cluster attach $dcos_cluster_name

echo "Trying to login to $dcos_cluster_name..."
dcos auth login --username=$username --password=$password

python draw_service_interaction.py -u jupiter

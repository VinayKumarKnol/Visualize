#!/usr/bin/python
import argparse
import os
import json
import traceback
import subprocess
from string import Template
import logging
import requests
from git_commit_document import commit_file_to_repo
from graphviz import Digraph


def main(args):
    get_latest_configuration(args)
    service_config = load_config(service_config_file_name)
    starting_point = args.starting_point
    service_json = find_service_id(starting_point, service_config)
    diagram = Digraph(comment=args.dcos_cluster_name + " services interaction",
                      engine='circo',
                      node_attr={'shape': 'box'},
                      graph_attr={'splines': 'true', 'esep': '10'},
                      edge_attr={'labelangle': '0'}, format='png')
    all_es_hosts = get_elasticsearch_list(service_config)
    assoc_services = service_json['env']
    oculus_services = \
        get_associated_services(assoc_services, 'OCULUS',
                                service_config, starting_point)
    infosight_services = \
        get_associated_services(assoc_services, 'INFOSIGHT',
                                service_config, starting_point)
    infosight_es = get_es_of_api(infosight_services, all_es_hosts, service_config)
    oculus_es = get_es_of_api(oculus_services, all_es_hosts, service_config)

    diagram.node(starting_point)
    infosight_cluster = Digraph(comment="Infosight Cluster",
                                node_attr={'color': 'blue'})
    oculus_cluster = Digraph(comment="Oculus Cluster", node_attr={'color': 'red'})
    es_cluster = Digraph(comment="Elasticsearch Cluster", node_attr={'color': 'green'})

    infosight_cluster = add_nodes_to_graph(infosight_cluster, infosight_services)
    oculus_cluster = add_nodes_to_graph(oculus_cluster, oculus_services)
    es_cluster = add_es_nodes_to_graph(es_cluster, infosight_es)
    es_cluster = add_es_nodes_to_graph(es_cluster, oculus_es)

    diagram.subgraph(infosight_cluster)
    diagram.subgraph(oculus_cluster)
    diagram.subgraph(es_cluster)

    diagram = add_nodes_to_graph(diagram, oculus_services)
    diagram = add_es_nodes_to_graph(diagram, infosight_es)
    diagram = add_es_nodes_to_graph(diagram, oculus_es)
    diagram = add_edge_to_graph(diagram, infosight_services)
    diagram = add_edge_to_graph(diagram, oculus_services)
    diagram = add_es_edge_to_graph(diagram, oculus_es)

    diagram.render(file_name, view=False)

    commit_file_to_repo(username=args.git_username,
                        repo=args.git_repo,
                        client_id=args.git_client_id,
                        client_secret=args.git_client_secret,
                        file_location=file_name + '.png',
                        branch=args.git_branch)

    return


def add_es_edge_to_graph(digraph, services):
    for parent, middle, child in services:
        digraph.edge(parent, child, label=middle, constraint='false', decorate='true')
    return digraph


def add_edge_to_graph(digraph, services):
    for parent, child in services:
        digraph.edge(str(parent), str(child), constraint='false')
    return digraph


def add_es_nodes_to_graph(digraph, es_nodes):
    for parent, service, es_name in es_nodes:
        if es_name is not None:
            digraph = add_nodes_to_graph(digraph, [(parent, es_name)])
    return digraph


def add_nodes_to_graph(digraph, distinct_services):
    # input:
    #   digraph: this is the visualization object.
    #   distinct_services: takes all the services which are related.
    # takes the list of all the services and adds them to visualization as nodes.
    # output:
    #   digraph: updated visual object.
    for service in distinct_services:
        if service is not None:
            digraph.node(str(service[1]))
    return digraph


def get_name_of_es_host(es_host, known_es_hosts):
    # input:
    #   es_host: es hosts we want to know the name of.
    #   known_es_hosts: list of known hosts with their names.
    # finds the es_hosts in the known hosts list since we have all hosts' name in the es.
    # output:
    #   name: the name returned of the es host.

    for name, es_hosts in known_es_hosts.items():
        if es_host == es_hosts:
            return name


def get_es_of_api(services_list, all_es_hosts, service_config):
    # input:
    #  services_list : list of service where we need to fine the es.
    #  all_es_hosts  : to find the name of found es hosts.
    #  service_config: contains the json of service.
    # gets the es host associated with service and categorise them as follows
    #   (parent_service, child_service, es_name)
    # Output:
    #  linked_es: contains the list of related es with the services.

    linked_es = []
    pattern = 'ELASTICSEARCH_HOSTS_'
    for parent, service_id in services_list:
        if service_id is not None:
            service_json = find_service_id(service_id, service_config)
            if 'env' in service_json:
                for service, es_hosts in service_json['env'].items():
                    if pattern in service:
                        es_name = get_name_of_es_host(es_hosts, all_es_hosts)
                        if es_name is None:
                            es_name = get_elasticsearch_name(es_hosts)
                        linked_es.append((service_id, service.split(pattern)[1],
                                          es_name))
    return linked_es


def find_service_id(service_id, service_config):
    # input:
    #  service_id: the name of the service.
    #  service_config: the json object which has all the service details.
    # Looks for the service in the service_config and snips the json of
    # of the service with the given service_id.
    # output:
    #  service is returned if found. other wise None is returned. service contains the
    # json of service with the name service_id.

    for service in service_config:
        if service_id in service['id']:
            return service


def get_elasticsearch_list(service_config):
    # input: service_config contains the json of the service.
    # looks for the all unique hosts service are using and makes the array of it.
    # output: returns the dictionary object with key es host name and value as
    # es hosts.
    all_es_hosts = accumulate_all_elasticsearch(service_config)
    es_hosts_cluster_name = {}
    for es_host in all_es_hosts:
        es_hosts_cluster_name[get_elasticsearch_name(es_host)] = es_host
    return es_hosts_cluster_name


def get_elasticsearch_name(elastic_host):
    url = 'http://' + elastic_host.split(',')[0] + ':9200'
    response = json.loads(requests.get(url).content)
    return response['cluster_name']


def find_service_id_by_port(service_port, service_config):
    for service in service_config:
        if 'container' in service:
            if 'portMappings' in service['container']:
                for port_mapping in service['container']['portMappings']:
                    if service_port == port_mapping['servicePort']:
                        return service['id']


def get_associated_services(assoc_services, pattern, service_config, starting_point):
    # input:
    #  assoc_services: takes the list of ports of associated services.
    #  pattern: takes the Initial name of the service you are looking for.
    #             for e.g. ELASTICSEARCH_HOST or OCULUS.
    #  service_config: json of all the services.
    #  starting_point: the starting point from where we started.
    # looks for the service associated by searching the json. We call it match if:
    #   the servicePort of service matches the port defined in assoc_services list.
    # Output: the dict object where
    #  key -> starting_point value -> service_id which was matched.

    services = list()
    for key in assoc_services.keys():
        if pattern in key:
            try:
                services.append((starting_point,
                                 find_service_id_by_port(int(assoc_services[key].split(':')[1]), service_config)
                                 ))
            except IndexError:
                print "Service called: %s doesn't have associated services" % starting_point
    return services


def load_config(config_location):
    # input: config_location: relative location of the json file>
    # Loads the json file if the given locations is right.
    # output: the json object the given file.
    service_file = open(config_location, 'r')
    service_json = json.load(service_file)
    service_file.close()
    return service_json


def check_command_status(command_status):
    if command_status is not 0:
        logging.error("==Not able to connect to the cluster. check vpn/credentials")
        exit(1)
    else:
        return


def accumulate_all_elasticsearch(service_config):
    elastic_hosts = []
    pattern = 'ELASTICSEARCH_HOSTS_'
    for service in service_config:
        if 'env' in service:
            environment = service['env']
        for env_var in environment:
            if pattern in env_var:
                elastic_hosts.append(environment[env_var])
    return set(elastic_hosts)


def get_latest_configuration(args):
    # input: args are command line arguments given.
    # Logs into the cluster with given credentials and fetches the service.json.
    # output: under conf/service.json the data is written in the file.
    if not os.path.exists(args.credentials):
        logging.warning('Location of credentials doesn\'t exist.'
                        ' Create credentials.json file')
        return
    else:
        script_dir = os.path.dirname(__file__)
        credentials_file_loc = os.path.join(script_dir, args.credentials)
        with open(credentials_file_loc, 'r') as credentials:
            credentials = json.load(credentials)
            print("==Trying to connect to dcos cluster "
                  + args.dcos_cluster_name)
            command = clusterAttach.substitute(dcos_cluster_name=args.dcos_cluster_name)
            check_command_status(subprocess.call(command.split(' ')))

            command = authLogin.substitute(username=credentials['login']['username'],
                                           password=credentials['login']['password'])
            check_command_status(subprocess.call(command.split(' ')))

            print ("==Getting the marathon json from cluster")
            command_out = subprocess.check_output(getConfig.split(' '))
            outFile_conf = open(service_config_file_name, 'w')
            outFile_conf.write(command_out)
            outFile_conf.close()
            print \
                ("==json is now available at conf/service.json.")


def parseArgs():
    parser = argparse.ArgumentParser(description='Python service visualization engine')
    parser.add_argument('-c', '--credentials', type=str, required=True,
                        help='location of user credentials file required to login.')
    parser.add_argument('-u', '--dcos_cluster_name', type=str, required=True,
                        help='Cluster whose service interaction visualization'
                             ' is required.')
    parser.add_argument('-s', '--starting_point', type=str, required=True,
                        help='nginx service to start analysis from.')
    parser.add_argument('-gu', '--git_username', type=str, required=True,
                        help='your github id.')
    parser.add_argument('-gr', '--git_repo', type=str, required=True,
                        help='github repo to commit to.')
    parser.add_argument('-gb', '--git_branch', type=str, required=True,
                        help='github branch to commit to.')
    parser.add_argument('-gcid', '--git_client_id', type=str, required=True,
                        help='github oauth client id .')
    parser.add_argument('-gcs', '--git_client_secret', type=str, required=True,
                        help='github oauth client secret.')
    args = parser.parse_args()
    return args


args = parseArgs()
clusterAttach = Template('dcos cluster attach $dcos_cluster_name')
authLogin = Template('dcos auth login --username=$username --password=$password')
getConfig = 'dcos marathon app list --json'
file_name = 'meta/service_arch'
service_config_file_name = 'conf/service.json'

if __name__ == '__main__':
    exit(main(args))

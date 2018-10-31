#!/usr/bin/python
import argparse
import os
import json
import traceback
import subprocess
from string import Template
import logging
import requests
from graphviz import Digraph


def main(args):
    # get_latest_configuration(args)
    # print find_service_id_by_port(5000, service_config)
    # print assoc_services.keys()
    service_config = load_config('conf/service.json')
    starting_point = '/nginx-beta-infosight'
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
    # print oculus_services
    infosight_services = \
        get_associated_services(assoc_services, 'INFOSIGHT',
                                service_config, starting_point)
    # print infosight_services
    infosight_es = get_es_of_api(infosight_services, all_es_hosts, service_config)
    # print infosight_es
    oculus_es = get_es_of_api(oculus_services, all_es_hosts, service_config)
    # print oculus_es

    diagram.node(starting_point)
    infosight_cluster = Digraph(comment="Infosight Cluster",
                                node_attr={'color':'blue'})
    oculus_cluster = Digraph(comment="Oculus Cluster", node_attr={'color':'red'})
    es_cluster = Digraph(comment="Elasticsearch Cluster", node_attr={'color':'green'})

    infosight_cluster = add_nodes_to_graph(infosight_cluster, infosight_services)
    oculus_cluster = add_nodes_to_graph(oculus_cluster, oculus_services)
    es_cluster = add_es_nodes_to_graph(es_cluster, infosight_es)
    es_cluster = add_es_nodes_to_graph(es_cluster, oculus_es)

    diagram.subgraph(infosight_cluster)
    diagram.subgraph(oculus_cluster)
    diagram.subgraph(es_cluster)

    # oculus_cluster = add_edge_to_graph(oculus_cluster, oculus_services)
    # infosight_cluster = add_edge_to_graph(infosight_cluster, infosight_services)
    # es_cluster = add_es_edge_to_graph(diagram, oculus_es)
    # es_cluster = add_es_edge_to_graph(diagram, infosight_es)
    diagram = add_nodes_to_graph(diagram, oculus_services)
    diagram = add_es_nodes_to_graph(diagram, infosight_es)
    diagram = add_es_nodes_to_graph(diagram, oculus_es)
    diagram = add_edge_to_graph(diagram, infosight_services)
    diagram = add_edge_to_graph(diagram, oculus_services)
    diagram = add_es_edge_to_graph(diagram, oculus_es)


    diagram.render('meta/service_arch', view=False)

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
        digraph = add_nodes_to_graph(digraph, [(parent, es_name)])
    return digraph


def add_nodes_to_graph(digraph, distinct_services):
    for service in distinct_services:
        if service is not None:
            digraph.node(str(service[1]))
    return digraph


def get_name_of_es_host(es_host, known_es_hosts):
    for name, es_hosts in known_es_hosts.items():
        if es_host == es_hosts:
            return name


def get_es_of_api(services_list, all_es_hosts, service_config):
    linked_es = []
    pattern = 'ELASTICSEARCH_HOSTS_'
    for parent, service_id in services_list:
        if service_id is not None:
            service_json = find_service_id(service_id, service_config)
            if 'env' in service_json:
                for service, es_hosts in service_json['env'].items():
                    # print service, es_hosts
                    if pattern in service:
                        es_name = get_name_of_es_host(es_hosts, all_es_hosts)
                        # print es_name
                        linked_es.append((service_id, service.split(pattern)[1],
                                          es_name))
    return linked_es


def find_service_id(service_id, service_config):
    for service in service_config:
        if service_id in service['id']:
            return service


def get_elasticsearch_list(service_config):
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
            # print service['container']
            if 'portMappings' in service['container']:
                for port_mapping in service['container']['portMappings']:
                    if service_port == port_mapping['servicePort']:
                        return service['id']


def get_associated_services(assoc_services, pattern, service_config, starting_point):
    services = list()
    for key in assoc_services.keys():
        if pattern in key:
            # print assoc_services[key].split(':')[1]
            services.append((starting_point,
                             find_service_id_by_port(int(assoc_services[key].split(':')[1]), service_config)
                             ))
    return services


def load_config(config_location):
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
    if not os.path.exists(args.credentials):
        logging.warning('Location of credentials doesn\'t exist.'
                        ' Create credentials.json file')
        return
    else:
        script_dir = os.path.dirname(__file__)
        # print script_dir
        credentials_file_loc = os.path.join(script_dir, args.credentials)
        # print credentials_file_loc
        with open(credentials_file_loc, 'r') as credentials:
            credentials = json.load(credentials)
            # print credentials
            print("==Trying to connect to dcos cluster "
                  + args.dcos_cluster_name)
            command = clusterAttach.substitute(dcos_cluster_name=args.dcos_cluster_name)
            check_command_status(subprocess.call(command.split(' ')))

            command = authLogin.substitute(username=credentials['sahil.sawhney']['username'],
                                           password=credentials['sahil.sawhney']['password'])
            check_command_status(subprocess.call(command.split(' ')))

            print ("==Getting the marathon json from cluster")
            command_out = subprocess.check_output(getConfig.split(' '))
            outFile_conf = open('conf/service.json', 'w')
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
                             ' are required')
    args = parser.parse_args()
    return args


args = parseArgs()
clusterAttach = Template('dcos cluster attach $dcos_cluster_name')
authLogin = Template('dcos auth login --username=$username --password=$password')
getConfig = 'dcos marathon app list --json'

if __name__ == '__main__':
    exit(main(args))

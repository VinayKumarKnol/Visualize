#!/usr/bin/python
import argparse
import os
import json
import traceback
import subprocess
from string import Template
import logging
import requests


def main(args):
    # get_latest_configuration(args)
    # print find_service_id_by_port(5000, service_config)
    # print assoc_services.keys()
    service_config = load_config('conf/service.json')
    starting_point = '/nginx-qa-infosight'
    service_json = find_service_id(starting_point, service_config)

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

    return


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

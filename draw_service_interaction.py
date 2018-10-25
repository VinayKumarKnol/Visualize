#!/usr/bin/python
import argparse
import os
import json
import traceback
import subprocess
from string import Template
import logging


def main(args):
    # getLatestConfiguration(args)
    return


def checkCommandStatus(command_status):
    if command_status is not 0:
        logging.error("==Not able to connect to the cluster. check vpn/credentials")
        exit(1)
    else:
        return


def getLatestConfiguration(args):
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
            checkCommandStatus(subprocess.call(command.split(' ')))

            command = authLogin.substitute(username=credentials['sahil.sawhney']['username'],
                                           password=credentials['sahil.sawhney']['password'])
            checkCommandStatus(subprocess.call(command.split(' ')))

            print ("==Getting the marathon json from cluster")
            command_out = subprocess.check_output(getConfig.split(' '))
            outFile_conf = open('conf/service.json', 'w')
            outFile_conf.write(command_out)
            outFile_conf.close()
            print\
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

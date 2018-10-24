#!/usr/bin/python
import argparse
import os
import json
import traceback
import subprocess
from string import Template
import logging


def main(args):
    getLatestConfiguration(args)
    return


def getLatestConfiguration(args):
    if not os.path.exists(args.credentials):
        logging.warning('Location of credentials doesn\'t exist.'
                        ' Create credentials.json file')
        return
    else:
        logging.info("==Getting the marathon json from cluster")
        command_out = subprocess.check_output(getConfig.split(' '))
        outFile_conf = open('conf/service.json', 'w')
        outFile_conf.write(command_out)
        outFile_conf.close()
        logging.info("==json is now available at conf/service.json.")


def parseArgs():
    parser = argparse.ArgumentParser(description='Python service visualization engine')
    # parser.add_argument('-c', '--credentials', type=str, required=True,
    #                     help='location of user credentials file required to login.')
    # parser.add_argument('-u', '--dcos_cluster_name', type=str, required=True,
    #                     help='Cluster whose service interaction visualization'
    #                          ' are required')
    # args = parser.parse_args()
    return args


args = parseArgs()
clusterAttach = Template('dcos cluster attach $dcos_cluster_name')
authLogin = Template('dcos auth login --username=$username --password=$password')
getConfig = 'dcos marathon app list --json'

if __name__ == '__main__':
    exit(main(args))

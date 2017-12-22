#!/usr/local/bin/python3

##########################################################################
## Script Name    : get_paused_replicas.py                              ##
## Created        : 12/22/2017                                          ##
## Author         : John McDevitt                                       ##
## Function       : finds HDID active full copies in paused config      ##
##                :                                                     ##
## Usage          :                                                     ##
## Update Log     :                                                     ##
## Notes          : expects hdid_connection_info.json to exist.  Format:##
##    {                                                                 ##
##	"credentials": {                                                ##
##		"username": "USERNAME",                                 ##
##		"password": "PASSWORD",                                 ##
##		"space": "DOMAIN"                                       ##
##	},                                                              ##
##	"master": "MASTERSERVER"                                        ##
##    }                                                                 ##
##                                                                      ##
##                                                                      ##
##                                                                      ##
##########################################################################

##########################################################################
## Function definitions                                                 ##
##########################################################################
debug_val = 1

def debug(msg,debug_level=1):
    """Print debugging messages"""
    if debug_level >= debug_val:
        print("DEBUG" + str(debug_level) + ": " + str(msg))

##########################################################################
## Imports                                                              ##
##########################################################################

import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

##########################################################################
## Main                                                                 ##
##########################################################################

f = open('hdid_connection_info.json','r')
connection = json.load(f)
f.close

base_url = 'https://' + connection['master'] + '/HDID/v1.0.0/'
url_body={'username': connection['credentials']['username'],'password':connection['credentials']['password'] ,'space': connection['credentials']['space']}
headers= {'Content-Type': 'application/json'}

##########################################################################
## Login to HDID                                                        ##
##########################################################################

debug_level=0

url = base_url + 'master/UIController/services/User/actions/login/invoke'


response = requests.post(url,data=url_body, verify=False)
debug(str(response.status_code),debug_level)
if response.status_code > 200:
    debug(response.text,debug_level)

cookie=response.cookies.get_dict()
debug(str(cookie),debug_level)

##########################################################################
## Query all the replications that are Active Full Copy for Paused      ##
##########################################################################

debug_level=0

url = base_url + 'master/NodeManager/objects/Nodes/?query=(type+IN+("HitachiVirtualStoragePlatform"))&order-by=name+ASC'
debug(url,debug_level)

response = requests.get(url,cookies=cookie, verify=False)
debug(str(response.status_code),debug_level)
if response.status_code > 200:
    debug(response.text,debug_level)

json_nodes=json.loads(response.text)
for array in json_nodes['node']:
    #hbhs = []
    debug(str(array),debug_level)
    debug(array['id'],debug_level)
    url = base_url + array['id'] + '/VirtualStoragePlatformHandler/objects/Replications/'
    debug(url,debug_level)
    response = requests.get(url,cookies=cookie, verify=False)
    debug(str(response.status_code),debug_level)
    if response.status_code > 200:
        debug(response.text,debug_level)
    else:
        json_replications = json.loads(response.text)
        for replication in json_replications['replication']:
            debug(replication,debug_level)
            if replication['backupType'] == 'eACTIVE_FULL_COPY' and replication['pauseStatus']:
                debug('this replication impacted',debug_level)
                print('The replication for policy ' + replication['policyName'] + ' on node ' + replication['applicationHost'] + ' has operation ' + replication['operationName'] + ' paused.  Please investigate')



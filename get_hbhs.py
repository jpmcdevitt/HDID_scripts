#!/usr/local/bin/python3

##########################################################################
## Script Name    : get_hbhs.py                                         ##
## Created        :                                                     ##
## Author         : John McDevitt                                       ##
## Function       :                                                     ##
##                :                                                     ##
## Usage          :                                                     ##
## Update Log     : 12/22/2017 - externalized connection info           ##
## Notes          : expects hdid_connection_info.json to exist.  Format:##
##    {                                                                 ##
##      "credentials": {                                                ##
##              "username": "USERNAME",                                 ##
##              "password": "PASSWORD",                                 ##
##              "space": "DOMAIN"                                       ##
##      },                                                              ##
##      "master": "MASTERSERVER"                                        ##
##    }                                                                 ##
##                :                                                     ##
##########################################################################

##########################################################################
## Function definitions                                                 ##
##########################################################################

##########################################################################
## debug function                                                       ##
## takes a message (ensure it is a string) and optionally a debug level ##
## set debug level explicitly for higher level debug messages           ##
## set debug_val higher when you want the higher level messages printed ##
##########################################################################
debug_val = 1
def debug(msg,debug_level=1):
    """Print debugging messages"""
    if debug_level >= debug_val:
        print('DEBUG' + str(debug_level) + ': ' + str(msg))
        
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
debug(url,debug_level)

response = requests.post(url,data= url_body, verify=False)
debug(str(response.status_code),debug_level)
if response.status_code > 200:
    debug(response.text,debug_level)

cookie=response.cookies.get_dict()
debug(str(cookie),debug_level)

##########################################################################
## Get all of the existing HBHs, output to <serialnumber>.txt           ##
##########################################################################

debug_level=0

url = base_url + 'master/NodeManager/objects/Nodes/?query=(type+IN+(HardwareNodeBlock))&order-by=name+ASC'
debug(url,debug_level)

response = requests.get(url,cookies=cookie, verify=False)
debug(str(response.status_code),debug_level)
debug(response.text,debug_level)

json_nodes=json.loads(response.text)

debug_level=0

for node in json_nodes['node']:
    debug(str(node),debug_level)
    f = open(node['nodeAttributes'][0]['value'] + '.txt', 'a')
    url = base_url + 'master/HardwareNodeHandler/objects/HardwareNodes/' + node['id']
    debug(url,debug_level)
    response = requests.get(url,cookies=cookie, verify=False)
    debug(str(response.status_code),debug_level)
    if response.status_code > 200:
        debug(response.text,debug_level)
    f.write(response.text)
    f.close





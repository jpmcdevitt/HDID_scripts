#!/usr/local/bin/python3

##########################################################################
## Script Name    : create_hbh_input.py                                 ##
## Created        : 12/15/2017                                          ##
## Author         : John McDevitt                                       ##
## Function       : generate sample input for create_hbh.py script      ##
##                :                                                     ##
## Usage          :                                                     ##
## Update Log     :                                                     ##
##                :                                                     ##
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
debug(url,debug_level)

response = requests.post(url,data=url_body, verify=False)
debug(str(response.status_code),debug_level)
if response.status_code > 200:
    debug(response.text,debug_level)

cookie=response.cookies.get_dict()
debug(str(cookie),debug_level)

##########################################################################
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
    hbhs = []
    debug(str(array),debug_level)
    debug(array['id'],debug_level)
    url = base_url + array['id'] + '/VirtualStoragePlatformHandler/objects/HostGroups?query=(name+!~+%22-g00%22)&order-by=name+ASC'
    debug(url,debug_level)
    response = requests.get(url,cookies=cookie, verify=False)
    debug(str(response.status_code),debug_level)
    if response.status_code > 200:
        debug(response.text,debug_level)
    else:
        json_hostgroups = json.loads(response.text)
        for hostgroup in json_hostgroups['hostGroup']:
            debug(hostgroup,debug_level)
            hbh = {}
            if hostgroup['name'] == 'HDIDProvisionedHostGroup':
                continue
            hbh = {'name':'HBH_' + hostgroup['name'] + '_' + hostgroup['storageIdentifier']}
            ldev = {'lDev' : hostgroup['port']} 
                        
            try:
                debug('comparing ' + hbhs[-1]['name'] + ' with ' + hbh['name'],debug_level)
                if hbhs[-1]['name'] == hbh['name']:
                    hbhs[-1]['dataSet'].append(ldev)
                    continue
            except IndexError:
                pass

            hbh['dataSet'] = []
            hbh['dataSet'].append(ldev)
            hbhs.append(hbh)
    debug(hbhs,debug_level)
    f = open(array['nodeAttributes'][0]['value'] + '_create.txt','w')
    json.dump(hbhs,f,indent=4)
    f.close



#!/usr/local/bin/python3

##########################################################################
## Script Name    : scheduled_restore.py                                ##
## Created        : 2017-12-27 16:55                                    ##
## Author         : John McDevitt                                       ##
## Function       : 2017-12-27 16:57                                    ##
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

response = requests.post(url,data=url_body, verify=False)
debug(str(response.status_code),debug_level)
if response.status_code > 200:
    debug(response.text,debug_level)

cookie=response.cookies.get_dict()
debug(str(cookie),debug_level)

##########################################################################
## Get all of the active dataflows that have restore in their name      ##
##########################################################################

debug_level=0

url = base_url + 'master/DataFlowHandler/objects/ActiveDataFlows/?query=(data.name~"restore")&order-by=data.name+ASC'
debug(url,debug_level)

response = requests.get(url,cookies=cookie, verify=False)
debug(str(response.status_code),debug_level)
if response.status_code > 200:
    debug(response.text,debug_level)

json_dataflows=json.loads(response.text)
for dataflow in json_dataflows['dataflow']:
    debug(str(dataflow),debug_level)
    ##########################################################################
    ## Get Policy name and the repository that's labeled for restore        ##
    ##########################################################################
    for connection in dataflow['data']['connections']:
        if connection['label'] == "RESTORE":
            repository_number = connection['destination']
            policy_id = connection['routedPolicies'][0]
    for node in dataflow['data']['nodes']:
        if node['id'] == repository_number:
            debug(node['nodeId'] + " is the node identified as restore source",debug_level)
            repository_guid = node['nodeId']

    debug_level=0
    debug("getting policy name and restore repo name",debug_level)
    debug("policy " + policy_id,debug_level)
    debug("repo " + repository_guid,debug_level)
    
    debug_level=0
    url = base_url + 'master/PolicyHandler/objects/Policies/' + policy_id
    debug(url,debug_level)
    response = requests.get(url,cookies=cookie, verify=False)
    debug(str(response.status_code),debug_level)
    if response.status_code > 200:
        debug(response.text,debug_level)
    json_policy=json.loads(response.text)
    debug(json.dumps(json_policy,indent=4),debug_level)
    restore_target = json_policy['description'].replace('RESTORE TO ','')
    debug('Restore target is ' + restore_target,debug_level)

    debug_level=0
    url = base_url + 'master/NodeManager/objects/Nodes/?query=(name="' + restore_target + '")'
    debug(url,debug_level)
    response = requests.get(url,cookies=cookie, verify=False)
    debug(str(response.status_code),debug_level)
    if response.status_code > 200:
        debug(response.text,debug_level)
    json_target=json.loads(response.text)
    debug(json_target['node'][0]['id'],debug_level)


    debug_level=0
    url = base_url + 'master/NodeManager/objects/Nodes/' + repository_guid
    debug(url,debug_level)
    response = requests.get(url,cookies=cookie, verify=False)
    debug(str(response.status_code),debug_level)
    if response.status_code > 200:
        debug(response.text,debug_level)
    json_node=json.loads(response.text)

    ##########################################################################
    ## use the policy name and the repository node ID to query for restore  ##
    ##########################################################################

    debug_level=0
    url = base_url + 'master/MetaDataAggregator/objects/FullRecoverableData/?query=(policyName~"' + json_policy['name'] + '")+AND+(storageNodeId~"' + json_node['name'] + '")&count=1&offset=0&order-by=captureDate+DESC'
    debug(url,debug_level)

    response = requests.get(url,cookies=cookie, verify=False)
    debug(str(response.status_code),debug_level)
    if response.status_code > 200:
        debug(response.text,debug_level)
    json_response=json.loads(response.text)
    
    ##########################################################################
    ## perform the restore to the designated target with most recent backup ##
    ##########################################################################

    debug_level=0
    url = base_url + 'master/RestoreHandler/services/Restores/actions/restore/invoke'
    filesystem_parameters = {}
    filesystem_parameters['destination']={}
    filesystem_parameters['destination']['destinationNodeId']=json_target['node'][0]['id']
    filesystem_parameters['collisionPolicy']='eRH_CP_OVERWRITERENAME'
    filesystem_parameters['recoverableData']=[]
    filesystem_parameters['recoverableData'].append({})
    filesystem_parameters['recoverableData'][0]['storageLocationName']=json_response['fullRecoverableData'][0]['storageLocationType']
    filesystem_parameters['recoverableData'][0]['storageNodeId']=json_response['fullRecoverableData'][0]['storageNodeId']
    filesystem_parameters['recoverableData'][0]['includeItems']=[]
    filesystem_parameters['recoverableData'][0]['includeItems'].append(json_response['fullRecoverableData'][0]['snapshotId'])
    url_data = {'fileSystemParameters' : filesystem_parameters, 'type':'eRH_DT_FILESYSTEM'}
    debug(json.dumps(url_data,indent=4),debug_level)


    debug_level=0
    response = requests.put(url,json=url_data,cookies=cookie,verify=False)
    debug(str(response.status_code),debug_level)
    if response.status_code > 202:
        debug(response.text,debug_level)
    
    jobid = response.json()
    debug(jobid,debug_level)
    
    debug_level=0
    
    url = base_url + 'master/JobStatusHandler/objects/Jobs/?query=(parentId="' + jobid['id'] + '")'
    response = requests.get(url,cookies=cookie, verify=False)
    debug(str(response.status_code),debug_level)
    if response.status_code > 200:
        debug(response.text,debug_level)
    
    job = response.json()
    debug(job,debug_level)
    print('Restore Job ' + str(job['job'][0]['id']) + ' has status ' + str(job['job'][0]['status']) + ' as of ' + str(job['job'][0]['timeCompleted']))

#!/usr/local/bin/python3

##########################################################################
## Script Name    : restore.py                                          ##
## Created        : 12/22/2017                                          ##
## Author         : John McDevitt                                       ##
## Function       : restores backup.zip from most recent backup using   ##
##                : policy master_backup.  performs restore on Pascal   ##
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
## Main                                                                 ##
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

base_url = 'https://' + connection['master'] + '/HDID/v6.0.0/'
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
## get the most recent backup of the master_backup policy for restore   ##
##########################################################################

debug_level=0

url_query = '?query=(storageLocationType="repository")+AND+(policyName="master_backup")&count=1&offset=0&order-by=captureDate+DESC/'
url = base_url + 'master/MetaDataAggregator/objects/FullRecoverableData/' + url_query

response = requests.get(url,cookies=cookie, verify=False)
debug(str(response.status_code),debug_level)
if response.status_code > 200:
    debug(response.text,debug_level)

json_response = json.loads(response.text)
debug(json_response['fullRecoverableData'][0]['snapshotId'],debug_level)

url = base_url + 'master/RestoreHandler/services/Restores/actions/restore/invoke'
filesystem_parameters = {}
filesystem_parameters['destination']={}
filesystem_parameters['destination']['destinationNodeId']='Pascal@B2-7822YP-ZO2SNU-SP3HDL-3R2AO4[0-1-5]'
filesystem_parameters['collisionPolicy']='eRH_CP_OVERWRITERENAME'
filesystem_parameters['recoverableData']=[]
filesystem_parameters['recoverableData'].append({})
filesystem_parameters['recoverableData'][0]['storageLocationName']=json_response['fullRecoverableData'][0]['storageLocationType']
filesystem_parameters['recoverableData'][0]['storageNodeId']=json_response['fullRecoverableData'][0]['storageNodeId']
filesystem_parameters['recoverableData'][0]['includeItems']=[]
filesystem_parameters['recoverableData'][0]['includeItems'].append(json_response['fullRecoverableData'][0]['snapshotId'] + '*c:*Program Files*Hitachi*HDID*backup.zip')
url_data = {'fileSystemParameters' : filesystem_parameters, 'type':'eRH_DT_FILESYSTEM'}
debug(json.dumps(url_data,indent=4),debug_level)

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
print('Job ' + str(job['job'][0]['id']) + ' has status ' + str(job['job'][0]['status']) + ' as of ' + str(job['job'][0]['timeCompleted']))

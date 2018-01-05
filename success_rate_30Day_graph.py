#!/usr/local/bin/python3

##########################################################################
## Script Name    : success_rate_graph.py                               ##
## Created        :                                                     ##
## Author         : Mark Hickey                                         ##
## Function       :                                                     ##
##                :                                                     ##
## Usage          :                                                     ##
## Update Log     : 01/04/2018 - initial version                        ##
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
## Basically, any debug message that has a debug_level lower than       ##
## debug_val is printed.  So when calling debug, use higher debug_level ##
## values for more verbose messages, etc.                               ##
##########################################################################
debug_val = 1
def debug(msg,debug_level):
    """Print debugging messages"""
    if debug_level <= debug_val:
        print('DEBUG' + str(debug_level) + ': ' + str(msg))
        
def usage():
    print("success_rate_30day_graph [-s YYYY-0MM-DD] [-e YY-MM-DD] -h")
        
##########################################################################
## Imports                                                              ##
##########################################################################

import sys
import getopt
import time
import datetime
from datetime import date
import calendar
import requests
import json
import urllib3
import plotly as py
import plotly.plotly as ppy
import plotly.graph_objs as go


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

##########################################################################
## Main                                                                 ##
##########################################################################

f = open('hdid_connection_info.json','r')
connection = json.load(f)
f.close

#
# handle inputs.  Should be -s YYYY-MM-DD and/or -e YY-MM-DD
# with no args, creates a graph of the last 30 days
# with just -e, creates a graph of the 30 days prior to an includeind the -e arg
# with just -s, creates a graph of everything from the -s arg forward (be careful
# with this one)
# 
got_end_date=0
got_start_date=0

try:
    opts, args = getopt.getopt(sys.argv[1:], "s:e:h")
except getopt.GetoptError as err:
    # print help information and exit:
    print(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)
output = None
verbose = False
for o, a in opts:
    if o == "-e":
        got_end_date=1
        end_date_str = a
        end_date_parts = end_date_str.split('-')
        end_date = datetime.date(int(end_date_parts[0]),int(end_date_parts[1]),int(end_date_parts[2]))
    elif o == "-s":
        got_start_date=1
        start_date_str = a
        start_date_parts = start_date_str.split('-')
        start_date = datetime.date(int(start_date_parts[0]),int(start_date_parts[1]),int(start_date_parts[2]))
    elif o == '-h':
        usage()
        sys.exit()
    else:
        assert False, "unhandled option"
        
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
debug(str(cookie),3)

#
# get the datetime for thirty days ago
#
if got_end_date == 0:
    end_date = date.today()
    end_date_str = end_date.isoformat()

if got_start_date == 0:
    td = datetime.timedelta(days=30)
    start_date = end_date - td
    start_date_str = start_date.isoformat()
    
print ("Start Date: " + start_date_str + " End Date: " + end_date_str)
#
#
# get some jobs
#

n_succeeds=0
n_fails=0
n_jobs=0
succ_pct=0
fail_pct=0
succ_tracex=[]
succ_tracey=[]
fail_tracex=[]
fail_tracey=[]
curr_date = "none"
offset=0
chunk=500
passed_start_date = 0
date_strings={}

while passed_start_date == 0:
    debug_level=1
    url = base_url + 'master/ReportHandler/objects/JobReports/0/collections/entries?count=' + str(chunk) + '&offset=' + str(offset) +'&order-by=timeStarted+DESC'
    debug(url,debug_level)
    offset +=chunk
    
    response = requests.get(url,cookies=cookie, verify=False)
    debug(str(response.status_code),debug_level)
    debug(response.text,2)
    json_jobs=json.loads(response.text)

    for job in json_jobs['job']:
        debug(job['description'],5)
        n_jobs +=1
        starttime = job['timeStarted']
        startdate = starttime[0:10]
        startdate_parts = startdate.split('-')
        startdate_date = datetime.date(int(startdate_parts[0]),int(startdate_parts[1]),int(startdate_parts[2]))
        
        #
        # Note that the code for skipping jobs outside of the date range depends on the 
        # job records being sorted in descending order by date.
        #
        if startdate_date > end_date:
            continue
       
            
        if startdate != curr_date:
            if curr_date == "none":
                curr_date = startdate
            else:
                debug("Got new date " + startdate +"; n_jobs: " + str(n_jobs) + "; n_succeeds: " + str(n_succeeds) + "; n_fails: " + str(n_fails),3)
                succ_pct = n_succeeds/(n_jobs-1) * 100
                
                fail_pct = n_fails/(n_jobs-1) * 100
                
                date_strings[curr_date] = {'tot_jobs':n_jobs,'succeeds':n_succeeds,'fails':n_fails,'succ_pct':succ_pct,'fail_pct':fail_pct}
                curr_date = startdate
                n_jobs=1
                n_succeeds = 0
                n_fails=0
                if startdate_date < start_date:
                    debug("breaking out of loop on date " + starttime,1)
                    passed_start_date=1
                    break
            
        debug(startdate,5)
        status= job['status']
        debug(status,5)
        if status == 'eJOB_SUCCEEDED':
            n_succeeds += 1
        elif status == 'eJOB_FAILED':
            n_fails += 1
            
# dump the hash
for d in date_strings.keys():
    debug ('Date: {0}: Success: {1:.1f} Fail: {2:1f}'.format(d,date_strings[d]['succ_pct'], date_strings[d]['fail_pct']),4)
    succ_tracey.append(date_strings[d]['succ_pct'])
    succ_tracex.append(d)
    fail_tracey.append(date_strings[d]['fail_pct'])
    fail_tracex.append(d)

# make a graph
succ_trace = go.Bar(x=succ_tracex,y=succ_tracey,name='Succeeded')
fail_trace = go.Bar(x=fail_tracex,y=fail_tracey,name='Failed')
data = [succ_trace, fail_trace]  
layout = go.Layout(barmode='stack',title="Success Rate %", xaxis=dict(tickangle=-90,autotick=False)) 
fig = go.Figure(data=data, layout=layout)
py.offline.plot(fig, filename='success_rates.html')      


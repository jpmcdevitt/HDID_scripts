#!/usr/local/bin/python3

##########################################################################
## Script Name    :                                                     ##
## Created        :                                                     ##
## Author         : John McDevitt                                       ##
## Function       :                                                     ##
##                :                                                     ##
## Usage          :                                                     ##
## Update Log     :                                                     ##
##                :                                                     ##
##########################################################################

##########################################################################
## Imports                                                              ##
##########################################################################

import sys
import requests
import json
import urllib3
from optparse import OptionParser

##########################################################################
## Parse commandline options                                            ##
##########################################################################

parser = OptionParser()
parser.add_option('-d', '--debug', type='int', dest='debug_level', help='set debug level')
parser.add_option("-v", action="store_true", dest="verbose")
parser.add_option("-q", action="store_false", dest="verbose")
(options,args) = parser.parse_args()

##########################################################################
## Function definitions                                                 ##
##########################################################################

if options.verbose:
    debug_val = 0
    ## if they ask for verbose, have every debug call print
elif options.verbose == False:
    debug_val = 50
    ## if they ask for quiet, make it require a really high debug level to trigger
else:
    debug_val = 1
    ## else, sane debug value 

def debug(msg,debug_level=1):
    """Print debugging messages"""
    if debug_level >= debug_val:
        print("DEBUG" + str(debug_level) + ": " + str(msg))
        
##########################################################################
## Main                                                                 ##
##########################################################################

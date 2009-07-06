#!/usr/bin/python -u

"""*
 * Copyright 2009 University of Victoria
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * """


__VERSION__ = '0.01'

import sys
import commands
import os
import logging
from cStringIO import StringIO
from optparse import OptionParser
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import xml
import subprocess
import commands
import re
import socket
# NAGIOS Plug-In API return code values

NAGIOS_RET_OK = 0
NAGIOS_RET_WARNING = 1
NAGIOS_RET_CRITICAL = 2
NAGIOS_RET_UNKNOWN = 3


def pluginExit(messageString, logString, returnCode):

	# ALRIGHT, so the log string is seperated by  my "delimiter" ';'
	# Thus, I'm going to assume the following log style format:

	# 2009-05-29 13:48:55,638 ; VMMemory ; INFO ; sl52base ; MEMORY ; 524288

	# The pertinent information should be located in the "4th col" and on
	# The 3rd col lists the "logger lvl", which I'm using to indicate
	# if it's standard plug-in output or an error

	outputString = StringIO()
	outputString.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
	
	# I need to check if ANY 'ERROR' log entries exist. If that's the case
	# then a different XML string should be formatted and sent out

        localIP = (socket.gethostbyaddr( socket.gethostname() ))[2][0]

	lines = logString.splitlines()
	for line in lines:
        	# If we encounter an 'error' entry in the logger, skip over it
		if (line.find("ERROR") != -1):
			returnCode = NAGIOS_RET_WARNING
			continue
		logStringEntries = line.split(';')
		#print logStringEntries
		
		outputString.write("<RESOURCE LOCATION=\""+localIP+"\" TYPE=\""+messageString+":" +logStringEntries[3].strip()+"\">")

		outputString.write("<ENTRY ID=\""+logStringEntries[4].strip()+"\">")
		outputString.write(logStringEntries[5].strip())
		outputString.write("</ENTRY>")
		outputString.write("</RESOURCE>")

	print messageString+" | "+ outputString.getvalue()
	sys.exit(returnCode)

class PluginObject:	

	def __init__(self, callingClass):
		self.logString = StringIO()
	
		self.logger = logging.getLogger(callingClass)
		self.logger.setLevel(logging.INFO)
		formatter = logging.Formatter('%(asctime)s ; %(name)s ; %(levelname)s ; %(message)s')
		xmlOutputHndlr = logging.StreamHandler(self.logString)
		xmlOutputHndlr.setFormatter(formatter)
		xmlOutputHndlr.setLevel(logging.INFO)

		errorOutputHndlr = logging.StreamHandler(sys.stdout)
		errorOutputHndlr.setFormatter(formatter)
		errorOutputHndlr.setLevel(logging.ERROR)

		self.logger.addHandler(xmlOutputHndlr)
		self.logger.addHandler(errorOutputHndlr)


class PluginCmdLineOpts(PluginObject):

        def __init__(self):
                PluginObject.__init__(self,self.__class__.__name__)
                # Parse command-line options.
                parser = OptionParser()


                #The following options are parsed to conform with Nagios Plug-In "standard practices"

                parser.add_option("-V","--version",dest="version", \
                        action="store_false", help="Diplay version information",default=True)
                parser.add_option("-v","--verbose",dest="verbosity",help="Set verbosity level (0-3)",default=0)
                #parser.add


                parser.add_option("--HNcon", action="callback", callback=HeadNodeVMIPs())
                parser.add_option("--HNvmmpool", action="callback", callback=HeadNodeVMMPools())
                parser.add_option("--HNnetpool", action="callback", callback=HeadNodeNetPools())         


                self.parser = parser

        # This method is also responsible for "picking" what resource to monitor via the appropriate
        # command line switches (which I need to define). I don't want a single, monolithic script
        # running for ALL the resources, since this waters down NAGIOS's monitoring capabilities
        # (since that would make only a single resource to monitor)
        # Instead, this one script will be executed multiple time with different commandline options
        # to facilitate the monitoring of the different resources independant of one another

        def validate(self):

                # Parse the command line arguments and store them in 'options'
                (options, args) = self.parser.parse_args()

                if not options.version:
                        self.logger.info('Plug-in Version #: '+ __VERSION__)
                        print __VERSION__

PERFORMANCE_DATA_LOC = "/tmp/service-perfdata"
TARGET_XML_FILE = "/tmp/mdsresource.xml"


class ResourceHandler(ContentHandler):
	def __init__(self): 
		 
		self.isResource = False
		self.isDomain = False
		self.collectedResources = {}
		self.repeatedEntry = False
	def startElement(self,name,attr):

		if name == 'RESOURCE':
			self.topLevelKey = attr.getValue('LOCATION')
			self.secondLevelKey = attr.getValue('TYPE')
				
			if(self.topLevelKey not in self.collectedResources.keys()):
				self.collectedResources[self.topLevelKey] = {}
			if(self.secondLevelKey not in self.collectedResources[self.topLevelKey].keys()):
				self.collectedResources[self.topLevelKey][self.secondLevelKey] = {}
			self.isResource = True
		elif name == 'DOMAIN':
			self.isDomain = True
			self.thirdLevelKey = attr.getValue('ID')
			if(self.thirdLevelKey in self.collectedResources[self.topLevelKey][self.secondLevelKey].keys()):
				self.repeatedEntry = True
	def characters (self, ch):
		if self.isDomain == True and self.repeatedEntry == False:
			self.collectedResources[self.topLevelKey][self.secondLevelKey][self.thirdLevelKey] = ch
		
	def endElement(self, name):
		if name == 'RESOURCE':
			self.isResource = False
		elif name == 'DOMAIN':
			self.isDomain = False
			self.repeatedResource = False
	def getResources(self):
		return self.collectedResources
		
#def ping(hostaddress):
	
	#retVal = False
 #      	ping = subprocess.Popen(["ping -c 2",hostaddress],stdout = subprocess.PIPE,stderr = subprocess.PIPE)
  #     	out, error = ping.communicate()
#	if(error != ""):
		#self.logger.error(error)
#		return False
 #      	return True

#        pinger = os.popen("ping -q -c2 "+hostaddress,"r")
 #       retVal = False
  #      while True:
 #               rx = pinger.readline()
 #               if not rx:
 #                       break
 #               rx.strip()
#                retVale = True

 #       pinger.close()
 #       return retVal

#ping("www.google.ca")
#myProc = NagiosPerfDataProcessor()
#parsedData = myProc.parse()

IJ_LOCATION = "/opt/sun/javadb/bin/ij"
SQL_IP_SCRIPT = "derbyUsedIPs.sql"
class HeadNodeVMIPs(PluginObject):

	def __init__(self):
		PluginObject.__init__(self,self.__class__.__name__)
	
	def __call__(self, option, opt_str, value, parser):
	
	#	__call__()
	
	#def __call__(self):
		print "I was called"
		query = IJ_LOCATION+ " "+SQL_IP_SCRIPT
		status, output = commands.getstatusoutput(query)
		#print status
		#print "printing output from query"
		#print output
		derbyIPs = []
		patt = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})") 
		for line in output.split():
			myRe = patt.search(line)
			if(myRe):
				derbyIPs.append({line.strip(): False})	
		
		for remoteVM in derbyIPs:
			#pass
			# There should be only 1 key in the dictionary structure
			# the '[0]' extracts the IP address as a string
			addr = remoteVM.keys()[0]
			if(self.ping(addr)):
				derbyIPs[derbyIPs.index(remoteVM)][addr] = True	
		
		for foundVM in derbyIPs:
			# Again, there should be only 1 'value' for a given key
			# and the 'value' is a True/False boolean
			if not (foundVM.values()):
				self.logger.error("Unable to reach VM!")
			
		print derbyIPs
		return derbyIPs	
		
	def ping(self, hostaddress):
		#print hostaddress
       
	        ping = subprocess.Popen(["ping","-c","1",hostaddress],stdout = subprocess.PIPE,stderr = subprocess.PIPE)
	        out, error = ping.communicate()
	        if(error != ""):
        	        self.logger.error(error)
               		return False
        	return True

GLOBUS_LOC = os.environ['GLOBUS_LOCATION']
#The "NIMBUS_" entries are relative to the GLOBUS_LOC var
NIMBUS_CONF = "/etc/nimbus/workspace-service"
NIMBUS_NET_CONF = "/network-pools"
NIMBUS_PHYS_CONF = "/vmm-pools"


class HeadNodeVMMPools(PluginObject):
 	 
	def __init__(self):
                PluginObject.__init__(self,self.__class__.__name__)
		self.resourceName = "VMM-Pools"

        def __call__(self, option, opt_str, value, parser):
		vmmPools = os.listdir(GLOBUS_LOC+NIMBUS_CONF+NIMBUS_PHYS_CONF)

		netPools = os.listdir(GLOBUS_LOC+NIMBUS_CONF+NIMBUS_NET_CONF)
		poolListing = {}
		
		for pool in vmmPools:
			
			#print "This pool is named: "+pool
			# Ignore "dot" file/folders - hidden directories
        		if(pool.startswith(".")):
                		continue
	                totalNetPools = {"ANY":0}
        	        for npool in netPools:
                	        if(npool.startswith(".")):
                       	         	continue
                       		totalNetPools.update({npool:0})
			try:
                		# I need to ignore the . hidden dirs
                		fileHandle = open(GLOBUS_LOC+NIMBUS_CONF+NIMBUS_PHYS_CONF+"/"+pool)
                		workerNodes = []
                		for entry in fileHandle:
                        		if(entry.startswith("#") or entry.isspace()):
                                		continue
					t = entry.split()
					workerNodes.append(t)
				fileHandle.close()
				for entry in workerNodes:
					# IF there is only 2 entries on this given line, that means
					# the particular workerNode has no specific network pool 
					# configured, so it's memory count gets added to the "global"
					# or DEFAULT count
					keyList = []
					if(len(entry)< 3):
						keyList.append("ANY")
					else:
	
						keyList = entry[2].split(",")
					for network in keyList:

						if( network == "*"):
							totalNetPools["ANY"] += int(entry[1])
							continue
						
						if network in (totalNetPools.keys()):
							totalNetPools[network] += int(entry[1])			
						else:
							self.logger.error("Erroneous entry in the VMM configuration: "+ network+" - Ignoring")
							#print "This is an erroneous entry!"
				poolListing[pool] = totalNetPools
			except IOError:
                                self.logger.error("Error opening vmm-pool: "+GLOBUS_LOC+NIMBUS_CONF+NIMBUS_PHYS_CONF+ pool)
                                sys.exit(NAGIOS_RET_CRITICAL)

		for key in poolListing.keys():
			for entry in totalNetPools.keys():
				self.logger.info(key+" ; "+entry+" ; "+str(poolListing[key][entry]))			
			
		pluginExit(self.resourceName, self.logString.getvalue(), NAGIOS_RET_OK)
		#print nodeTotals

class HeadNodeNetPools(PluginObject):

	def __init__(self):
		PluginObject.__init__(self, self.__class__.__name__)
		self.resourceName = "NetPools"


	def __call__(self, option, opt_str, value, parser):
		netPools = os.listdir(GLOBUS_LOC+NIMBUS_CONF+NIMBUS_NET_CONF)
		totalNetPools = []
	
		for pool in netPools:

			if(pool.startswith(".")):
				continue
			netPoolData = {}
			netPoolData["ID"] = pool
			try:
				fileHandle = open(GLOBUS_LOC+NIMBUS_CONF+NIMBUS_NET_CONF+"/"+pool)
				VMNetConfig = []
				
				for entry in fileHandle:
					if(entry.startswith("#") or entry.isspace()):
                                		continue
					t = entry.split()
					# This looks for the DNS server entry and skips over it
					# The config file stipulates that each line in the file must have
					# 5 entries for the net config, so I can use this condition to 
					# identify the lone DNS entry line
					if(len(t) < 5):
						#print t
						continue
					VMNetConfig.append(t)
				netPoolData["NETWORK"] = VMNetConfig				
				fileHandle.close()
				totalNetPools.append(netPoolData)
			except IOError:
				self.logger.error("Error opening network-pool: "+GLOBUS_LOC+NIMBUS_CONF+NIMBUS_NET_CONF+"/"+pool)
				sys.exit(NAGIOS_RET_ERROR)
		#print totalNetPools
		
		for dict in totalNetPools:
			sillyCount = 0
			for entry in dict["NETWORK"]:
				sillyCount +=1
				#print entry
			#print sillyCount
			# The first entry '-' seems silly but I need a placeholder for when the XML
			# is formatted on pluginExit to maintain homogeneity between the netPools and vmmPools code
			self.logger.info("-"+";"+dict["ID"]+";"+ str(sillyCount))

		pluginExit(self.resourceName, self.logString.getvalue(), NAGIOS_RET_OK)

testObject = PluginCmdLineOpts()
testObject.validate()

sys.exit(NAGIOS_RET_OK)

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
#import libvirt
from optparse import OptionParser
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import xml

# Python 2.3.* on gridxn doesn't support this... 
#import subprocess


# NAGIOS Plug-In API return code values

NAGIOS_RET_OK = 0
NAGIOS_RET_WARNING = 1
NAGIOS_RET_CRITICAL = 2
NAGIOS_RET_UNKNOWN = 3

NAGIOS_PERF_DATA_FILE = "/usr/local/nagios/service-perfdata"

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

	#if(logString.find("ERROR") == -1):
		# No 'ERROR' logging message recorded
		
	outputString.write("<RESOURCE>")
	lines = logString.splitlines()
	for line in lines:
        	# If we encounter an 'error' entry in the logger, skip over it
		if (line.find("ERROR") != -1):
			returnCode = NAGIOS_RET_WARNING
			continue
		logStringEntries = line.split(';')
		#print logStringEntries
		
		outputString.write("<DOMAIN ID=\'"+logStringEntries[3].strip()+"\'>")
		outputString.write("<"+logStringEntries[4].strip()+">")
		outputString.write(logStringEntries[5].strip())
		outputString.write("</"+logStringEntries[4].strip()+">")
		outputString.write("</DOMAIN>")
	outputString.write("</RESOURCE>")

	#else:
		# So 1 error means the whole plug-in run is "aborted" and no regular data will
		# be sent back to the server
	#	lines = logString.splitlines()
	#	for line in lines:
			#Does this 'line' contain an 'ERROR' logging msg?
	#		if line.find("ERROR")!= -1 :
	#			logStringEntries = line.split('|')
			
				# Thus, I need to 'find' the error string in the logString
	#			outputString.write("<ERROR>")
	#		outputString.write("[Class]: "+logStringEntries[1]+ " [Details]: "+logStringEntries[3])
	#		outputString.write("</ERROR>")

	print messageString+" | "+ outputString.getvalue()
	sys.exit(returnCode)

# No need to make this a class, since what's teh point of having a ctr
# that never finishes ctring... I'm going to call sys.exit() at the
# end, so the whole class/object bit is too heavyweight and uneccessary

#def pluginExit(messageString, logString,returnCode):

        # The idea is, when an "error" occurs and one would normally want to call
        # sys.exit. INSTEAD: call this function, pass in the object's logger and
        # the error message and then perform necessary formatting and output
        # to satisfy the NAGIOS plug-in API

        # The reason for this abstraction is to allow this script to properly
        # format the logger's error string for communication back to the NAGIOS
        # server. As a plug-in (in NAGIOS) MUST output some text and generally
        # follow the NAGIOS plug-in API, this centralizes the "error handling"

        # Since I'm toying with the idea of "presentation layer formatter" classes,
        # I can then instantiate one of these formatters, parse the log string
        # (stored in every class/object) and format it, then output it to stdout
        # (It's a NAGIOS plug-in remember). This outputted text will be sent
        # back to the monitoring daemon where it will be saved as "performance data"
        # This performance data will be processed by another script on the server so
        # the MDS Data Aggregator can then publish it

	
        # Recall the NAGIOS formatting of 'output' | 'performance data'
 #    	pluginOutput(messageString, logString)
#	sys.exit(returnCode)


class PluginObject:	

	def __init__(self, callingClass):
		self.logString = StringIO()
	#	logging.basicConfig(level=logging.DEBUG,  
	#				format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
	#			    	stream = self.logString)
	
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

class Virtualized(PluginObject):

        # Lookup the available "domains" from libvirt, and other usefull stuff
        def __init__(self):
                PluginObject.__init__(self,self.__class__.__name__)
                #Establish a connection to the local VM Hypervisor (XEN)
                self.VMConnection  = libvirt.openReadOnly(None)
                if self.VMConnection == None:
                        self.logger.error('Unable to open a Read-Only connection to local XEN Hypervisor')
                        pluginExit("VMConnection",self.logString.getvalue(), NAGIOS_RET_ERROR)
		
		# TODO - Remove Domain-0 from this list? I think so....

                self.VMDomainsID = self.VMConnection.listDomainsID()
                self.VMs={}
                for id in self.VMDomainsID:
                        #So, the VMs 'dictionary' stores virDomain (libvirt) objects
                        self.VMs[id] = (self.VMConnection.lookupByID(id))


# I'm using this class like a 'Functor' 

# I thought I'd have to define the __call__ function, but it seems like the 
# ctr is doing what I need it to for the 'Callback' functionality
class VMMemory(Virtualized):

	#This ctr's interface is as such to match the 'callback' interface of the optionParser
	def __init__(self): #,option, opt_str, value, parser):
		Virtualized.__init__(self)
		# This isn't strictly necessary....
		self.resourceName = 'MEMORY'

	def __call__(self, option, opt_str, value, parser):
        	for vm in self.VMs.values():
                	self.logger.info(vm.name()+' ; '+self.resourceName+ " ; %d", vm.maxMemory())

		self.logger.error("Shit on a biscuit!!")
		pluginExit("VM Memory/RAM Query", self.logString.getvalue(), NAGIOS_RET_OK)


class PluginCmdLineOpts(PluginObject):

	def __init__(self):
		PluginObject.__init__(self,self.__class__.__name__)
		# Parse command-line options.
		parser = OptionParser()

		#parser.add_option("--VMmem", action="callback", callback=VMMemory())
		#parser.add_option("--VMos", action="callback", callback=

		self.parser = parser

	# This method is also responsible for "picking" what resource to monitor via the appropriate
	# command line switches (which I need to define). I don't want a single, monolithic script
	# running for ALL the resources, since this waters down NAGIOS's monitoring capabilities
	# (since that would make only a single resource to monitor)
	# Instead, this one script will be executed multiple time with different commandline options
	# to facilitate the monitoring of the different resources independant of one another

	# Maybe I'll go back to my idea of a "dictionary of function pointers" so that the command line
	# switch can act as a key into the function map, so that the appropriate function can get
	# returned after a call to this method (and then one can execute said function)
	def validate(self):

		# Parse the command line arguments and store them in 'options'
		(options, args) = self.parser.parse_args()

#		if not options.version:
#    			self.logger.info('Plug-in Version #: '+ __VERSION__)

		# Check options for validity
#		verbose = int(options.verbosity)


#		if (verbose < 0) or (verbose > 3):
#			self.logger.error('Invalid verbosity option (Not in range 0-3)')
#			pluginExit(self,NAGIOS_RET_UNKNOWN)


# The "main" code starts here & begins execution here (I guess)

class NagiosPerfDataProcessor(PluginObject):

	def __init__(self):
		PluginObject.__init__(self,self.__class__.__name__)
		self.parser = make_parser()
		self.curHandler = ResourceHandler()
		self.parsedXML = ""
		self.totalResources = []
		self.parser.setContentHandler(self.curHandler)


	def parse(self):

		finalXML = StringIO()
		finalXML.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
		finalXML.write("<ROOT>")
		# TODO ERROR HANDLING & 'service-perfdata' location choice
		fileHandle = None	
		try:

			fileHandle = open(NAGIOS_PERF_DATA_FILE,"r")
			for line in fileHandle.readlines():
				# Ignore lines that don't contain the xml header that
				# our client plugins include as part of the transmission
				xmlHeaderIndex = line.find("<?xml")
				if (xmlHeaderIndex == -1):
					continue
				else:
					# This will only print the XML string from the found line
					#print line[xmlHeaderIndex:]
					# To find the 'end' of the xml header and effectively 
					# strip it off so the XML can be aggregated into 1 source
					tagIndex = line.find("?>") + 2
					#print line[tagIndex:]	
					resourceXMLEntry = line[tagIndex:]
					finalXML.write(resourceXMLEntry)

		except IOError:
			self.logger.error("Unable to open \'"+NAGIOS_PERF_DATA_FILE+"\' for reading!") 			
			sys.exit(NAGIOS_RET_CRITICAL)
		#finally:
		fileHandle.close()
		
		finalXML.write("</ROOT>")
		self.parsedXML=finalXML
		
		xml.sax.parseString(finalXML.getvalue(), self.curHandler)
		self.totalResources = self.curHandler.getResources()
		return self.totalResources
# This class implements the SAX API functions 'startElement', 'endElement' and 'characters'
# It is also intimately tied to the XML format used by the client side plugins

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

def ping(hostaddress):		

#	ping = subprocess.Popen(["ping","-c","3",host],stdout = subprocess.PIPE,stderr = subprocess.PIPE)
#	out, error = ping.communicate()
#	print out

	pinger = os.popen("ping -q -c2 "+hostaddress,"r")
	while True:	
		rx = pinger.readline()
		if not rx:
			break
		print rx.strip()

	pinger.close()
generatedData = NagiosPerfDataProcessor().parse()
ping("www.google.ca")
for ipaddress in generatedData.keys():
	print ipaddress
sys.exit(0)

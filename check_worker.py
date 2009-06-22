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
import libvirt
from optparse import OptionParser
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

	#if(logString.find("ERROR") == -1):
		# No 'ERROR' logging message recorded
	# TODO - Add error handling!
	localIP = (socket.gethostbyaddr( socket.gethostname() ))[2][0]
	
	resourceString = "<RESOURCE LOCATION=\""+ localIP+"\" TYPE=\""+messageString+"\">"
	outputString.write(resourceString)
	lines = logString.splitlines()
	for line in lines:
        	# If we encounter an 'error' entry in the logger, skip over it
		if (line.find("ERROR") != -1):
			returnCode = NAGIOS_RET_WARNING
			continue
		logStringEntries = line.split(';')
		#print logStringEntries
		
		outputString.write("<DOMAIN ID=\""+logStringEntries[3].strip()+"\">")

		outputString.write(logStringEntries[5].strip())
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
                        try:
				self.VMs[id] = (self.VMConnection.lookupByID(id))
			except:
				self.logger.error("Failed to lookup a VM from a VMConnection by \'id\'")
				pluginExit("Virtualized - Base Class",self.logString.getvalue(), NAGIOS_RET_ERROR)
# I'm using this class like a 'Functor' 

# I thought I'd have to define the __call__ function, but it seems like the 
# ctr is doing what I need it to for the 'Callback' functionality
class VMMemory(Virtualized):

	#This ctr's interface is as such to match the 'callback' interface of the optionParser
	def __init__(self): #,option, opt_str, value, parser):
		Virtualized.__init__(self)
		# This isn't strictly necessary....
		self.resourceName = 'VM-MEMORY'

	def __call__(self, option, opt_str, value, parser):
        	for vm in self.VMs.values():
                	self.logger.info(vm.name()+' ; '+self.resourceName+ " ; %d", vm.maxMemory())

		self.logger.error("Shit on a biscuit!!")
		pluginExit("VM-Memory", self.logString.getvalue(), NAGIOS_RET_OK)

class VMOs(Virtualized):

	def __init__(self):
		Virtualized.__init__(self)
		self.resourceName = "VM-OS"

	def __call__(self, option, opt_str, value, parser):
		for vm in self.VMs.values():
			self.logger.info(vm.name()+' ; '+self.resourceName+ " ; "+ vm.OSType())

		pluginExit("VM-OS", self.logString.getvalue(), NAGIOS_RET_OK)
		

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
		

		parser.add_option("--VMmem", action="callback", callback=VMMemory())
		parser.add_option("--VMos", action="callback", callback=VMOs())
	#	parser.add_option("--VM		


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
		

		# Check options for validity
		verbose = int(options.verbosity)
		if (verbose < 0) or (verbose > 3):
			self.logger.error("Invalid verbosity option (Not in range 0-3)")
			#pluginExit("Verbosity","",NAGIOS_RET_UNKNOWN)


# The "main" code starts here & begins execution here (I guess)

testObject = PluginCmdLineOpts()
testObject.validate()

#pluginExit(NAGIOS_RET_CRITICAL)

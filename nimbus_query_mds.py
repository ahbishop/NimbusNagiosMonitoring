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
import logging
from cStringIO import StringIO
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import xml
import subprocess
from subprocess import *

class Loggable:

        def __init__(self, callingClass):
                self.logString = StringIO()

                self.logger = logging.getLogger(callingClass)
                self.logger.setLevel(logging.INFO)
                formatter = logging.Formatter('%(asctime)s ; %(name)s ; %(levelname)s ; %(message)s')

                errorOutputHndlr = logging.StreamHandler(sys.stderr)
                errorOutputHndlr.setFormatter(formatter)
                errorOutputHndlr.setLevel(logging.ERROR)

                self.logger.addHandler(errorOutputHndlr)

		
# This class implements the SAX API functions 'startElement', 'endElement' and 'characters'
# It is also intimately tied to the XML format used by the client side plugins

class ResourceHandler(ContentHandler):
	def __init__(self): 
                self.isResource = False
                self.isEntry = False
	#	self.initializeList = True
                self.collectedResources = {}
                self.repeatedResource = False
        def startElement(self,name,attr):

                if name == 'RES':
                        self.topLevelKey = attr.getValue('LOC')
                        self.secondLevelKey = attr.getValue('TYPE')

                        if(self.topLevelKey not in self.collectedResources.keys()):
                                self.collectedResources[self.topLevelKey] = {}
                        if(self.secondLevelKey not in self.collectedResources[self.topLevelKey].keys()):
                                self.collectedResources[self.topLevelKey][self.secondLevelKey] = {}
                        self.isResource = True
                elif name == 'ENTRY':
                        self.isEntry = True
                        self.thirdLevelKey = attr.getValue('ID')
			identifiers = self.thirdLevelKey.split(":")
               #         if(self.initializeList == True):
#			self.collectedResources[self.topLevelKey][self.secondLevelKey][self.thirdLevelKey] = []	
	#			if(identifiers > 1):
	#				self.initializeList = False
			
			if(self.thirdLevelKey in self.collectedResources[self.topLevelKey][self.secondLevelKey].keys()):
                                self.repeatedResource = True
    			if(identifiers > 1):
				self.repeatedResource = False

        def characters (self, ch):
                if (self.isEntry == True and self.repeatedResource == False):
			#self.collectedResources[self.topLevelKey][self.secondLevelKey][self.thirdLevelKey].append( ch)
        		self.collectedResources[self.topLevelKey][self.secondLevelKey][self.thirdLevelKey] = ch
	def endElement(self, name):
                if name == 'RES':
                        self.isResource = False
	#		self.initializeList = True
                elif name == 'ENTRY':
                        self.isEntry = False
                        self.repeatedResource = False
        def getResources(self):
                return self.collectedResources


class MDSResourceException(Exception):

	def __init__(self, value):
		self.value = value
	
	def __str__(self):
		return repr(self.value)
		

# Get the XML string from the MDS registry first

SERVER_ADDRESS = "https://gridsn.phys.uvic.ca:8443/wsrf/services/DefaultIndexService"
XML_ROOT_TAG = "ROOT"

class MDSResourceQuery(Loggable):

	def __init__(self):
		Loggable.__init__(self,self.__class__.__name__)

	def __call__(self,serviceAddress, rootTag):
 
		# This argument string also contains an XPath query to extract the appropriate XML from
		# the XML/WebService response to querying the DefaultIndexService
		argString = "-s " + serviceAddress + " \"//*[local-name()='"+ rootTag +"']\""
		# The funny '.communicate()[0]' retrieves the stdout stream from the pipe so that the looked up
		# xml data can be brought into this script for processing
		try:
			
			process = subprocess.Popen("$GLOBUS_LOCATION/bin/wsrf-query "+argString, shell=True,stderr=PIPE, stdout=PIPE).communicate()
			# STDOUT from the command just executed
			retrievedXML = process[0]
			# STDERR from the command just executed
			retrievedError = process[1]
			
			# This was added since the exception handlers aren't being called
			if retrievedError != "":
				self.logger.error("Failed to execute external command :"+retrievedError)
				raise MDSResourceException("Failed to execute external command :"+retrievedError)
				#sys.exit(1)

		#These exception handlers aren't being called... Stupid python
		except Exception, e:
			self.logger.error("An unknown Exception has occured: "+e.getMessage())
			#self.exit(1)
			raise MDSResourceException("Unknown Exception has occured: "+e.getMessage())
		# According to the Python API docs, the subprocess.Popen command can throw an OSError or ValueError
		# but neither of these exception could be raised in testing (with Python 2.4.3)

		#except OSError:
		#	self.logger.error("OSError occured performning subprocess.Popen - Check 'wsrf-query' location")
		#	sys.exit(1)
		#except ValueError:
		#	self.logger.error("ValueError occured performing subprocess.Popen() - Check arguments")
		#	sys.exit(1)
		
		# Check to see if there was any results returned from the MDS
		# When the aggregator is unregistered, the query returns the string:
		# "Query did not return any results."
		# Thus, 'Query' is used for the 'find' call as it is the first word in the sentence 
		# (this isn't a requirement, any word could have been used really)
		if(retrievedXML.find("Query") != -1):
			print "Should be nothing returning from the MDS"
			raise MDSResourceException("No Resources in MDS Registry")

		xmlHandler = ResourceHandler()

		try:
			xml.sax.parseString(retrievedXML.strip(), xmlHandler)
		except xml.sax.SAXException, e:
			self.logger.error("Failed to parse retrieved XML: "+e.getMessage())	
			#sys.exit(1)
			raise MDSResourceException("Failed to parse retrieved XML: "+e.getMessage())
		self.postProcessing(xmlHandler.getResources())

		return xmlHandler.getResources()


	def postProcessing(self, resources):
		# OK, so I need to covert the "NetPools" information into an "availble" slots idea 
		# TODO THese are the WRONG IPs - they represent the physical node, not the VM
		utilizedIPs = resources.keys()
		

		print utilizedIPs
		queue = []
		totalIPs = []
		foundNetPools = False
		for entry in utilizedIPs:
			secondLevel= resources[entry].keys()
			#queue = []
			for secondEntry in secondLevel:
				if(secondEntry.find("NetPools")!=-1 and secondEntry !=("NetPools:Totals")):
					queue.append(secondEntry)
					# Yes this is evaluated multiple times...
					foundNetPools = True
			#print queue
			if(foundNetPools):
				for queueItem in queue:
					totalIPs.append(resources[entry][queueItem])
				# TODO uncomment below when not debugging
				#	del(resources[entry][queueItem])
				#print totalIPs
				foundNetPools = False 
		#print totalIPs
		filterSet = set()

		for entry in totalIPs:
			filterSet.add(entry.keys()[0])
		#print filterSet
		pools ={}
		for entry in filterSet:
			pools[entry]=[]

		for entry in totalIPs:
			pools[entry.keys()[0]].append(entry.values()[0])	
		print pools	
		#for entry in pools.keys():
		for ip in utilizedIPs:
			for key in pools.keys():
				if ip in pools[key]:
					pools[key].remove(ip)

		print pools


myQuery = MDSResourceQuery()

print myQuery(SERVER_ADDRESS,XML_ROOT_TAG)

sys.exit(0)

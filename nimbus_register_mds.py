#! /usr/bin/python

import os
import sys
import resource
import subprocess
from subprocess import *
#import signal
import time

REG_FILE = "mdsVirtReg.xml"
SERVER_ADDRESS = "https://gridsn.phys.uvic.ca:8443/wsrf/services/DefaultIndexService"
PID_PATH = "/tmp/nimbusMDSReg.pid"

#def daemonize (stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    # Perform first fork.
#	try:
#		pid = os.fork( )
#        	if pid > 0:
 #       		sys.exit(0) # Exit first parent.
#    	except OSError, e:
#        	sys.stderr.write("fork #1 failed: (%d) %sn" % (e.errno, e.strerror))
#        	sys.exit(1)
#    # Decouple from parent environment.
#	os.chdir("/")
#	os.umask(0)
#	os.setsid( )
	# Perform second fork.
#	try:
 #		pid = os.fork( )
  #      	if pid > 0:
 #           		sys.exit(0) # Exit second parent.
#	except OSError, e:
 #       	sys.stderr.write("fork #2 failed: (%d) %sn" % (e.errno, e.strerror))
#        	sys.exit(1)
    # The process is now daemonized, redirect standard file descriptors.
#	for f in sys.stdout, sys.stderr: 
#		f.flush( )
# 	si = file(stdin, 'r')
#    	so = file(stdout, 'a+')
#    	se = file(stderr, 'a+', 0)
#    	os.dup2(si.fileno( ), sys.stdin.fileno( ))
   # 	os.dup2(so.fileno( ), sys.stdout.fileno( ))
   # 	os.dup2(se.fileno( ), sys.stderr.fileno( ))

#def signalHandler(signum, frame):
#	print "Captured signal, terminating gracefully"
#	if(os.path.exists(PID_PATH)):
#		os.remove(PID_PATH)
def shat():
	try:
	
		if(os.path.exists(PID_PATH)):
			try:
				pidFile = open(PID_PATH,"r")
				pid = pidFile.readline()
				pidFile.close()
				print "A PID file exists (another instance is running)  with a PID of: "+pid
				sys.exit(0)	
			except IOError:
				print >>sys.stderr, "Error opening the PID file for reading at: ",PID_PATH
				sys.exit(-1)
		else:
			pid = os.getpid()
			try:
				pidFile = open(PID_PATH,"w")
				pidFile.write(str(pid))
				pidFile.close()
			except IOError:
				print >>sys.stderr, "Error opening the PID file for writing at: ",PID_PATH
				sys.exit(-1)
		
			argString = SERVER_ADDRESS + " " + REG_FILE 
			try:
				process = subprocess.Popen("/usr/local/globus-4.0.8/bin/mds-servicegroup-add -s "+argString , shell=True,stderr=PIPE, stdout=PIPE)
               			#sts = os.waitpid(process.pid, 0
				#time.sleep(7)
				#print process.poll()
				
				output = process.communicate()
				print >>sys.stdout, output[1], output[0]
				print "Sup sup?"
				if(os.path.exists(PID_PATH)):
					os.remove(PID_PATH)
			except OSError, e:
				print >>sys.stderr,"OSError encountered within the subprocess: ",e
				if(os.path.exists(PID_PATH)):
					os.remove(PID_PATH)
				sys.exit(-1)

	except KeyboardInterrupt:
		print "Terminating from a KeyboardInterrupt"
		if(os.path.exists(PID_PATH)):
                	os.remove(PID_PATH)

shat()




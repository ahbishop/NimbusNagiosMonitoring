#!/usr/bin/env python

import re
import sys

infoFile = open("/proc/cpuinfo","r")

nagiosRetCode = 2

for line in infoFile:
	matchedLine = re.search("(svm|vmx)",line)
	if matchedLine:
		print "Virtualization Extensions detected - ",
		nagiosRetCode = 0
		extensionType = matchedLine.string.find("svm")
		if extensionType == -1:
			print "Intel VMX"
		else:
			print "AMD SVM"
infoFile.close()
#print "Return type is ",
#print nagiosRetCode
sys.exit(nagiosRetCode)



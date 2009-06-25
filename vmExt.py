#!/usr/bin/env python
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



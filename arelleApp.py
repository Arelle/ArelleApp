'''
Created on May 16, 1013

This module is Arelle's entry point to initiate server app operation

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
import sys, os
# make the lib/svr directory accessible for module searching
sys.path.insert(1, os.path.join(sys.path[0],'lib','svr'))
import CntlrAppSvr
CntlrAppSvr.main()
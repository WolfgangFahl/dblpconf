'''
Created on 2021-01-25

@author: wf
'''
import unittest
from dblpconf.dblp import Dblp
import os
import time

class TestDblpConf(unittest.TestCase):
    '''
    test the dblp conferences access
    '''


    def setUp(self):
        self.debug=False
        pass


    def tearDown(self):
        pass


    def testDblpConf(self):
        '''
        test dblp access
        '''
        dblp=Dblp()
        xmlfile=dblp.getXmlFile()
        if self.debug:
            print("dblp xml file is %s " % xmlfile)
        self.assertTrue(os.path.isfile(xmlfile))
        stats=os.stat(xmlfile)
        self.assertTrue(stats.st_size>3000000000)
        pass
    
    def testParser(self):
        '''
        test parsing the xml file
        '''
        dblp=Dblp()
        xmlfile=dblp.getXmlFile()
        self.assertTrue(xmlfile is not None)
        index=0
        starttime=time.time()
        for _, elem in dblp.iterParser():
            index+=1
            if index%500000==0:
                elapsed=time.time()-starttime
                if self.debug:
                    print ("%8d: %5.1f s %5.0f/s %s" % (index,elapsed,index/elapsed,elem))
            elem.clear()    
        self.assertTrue(index>70000000)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
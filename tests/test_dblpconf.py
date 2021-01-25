'''
Created on 2021-01-25

@author: wf
'''
import unittest
from dblpconf.dblp import Dblp
import os

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


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
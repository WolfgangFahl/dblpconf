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
        self.debug=True
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
        dblp=Dblp(dtd_validation=False)
        xmlfile=dblp.getXmlFile()
        self.assertTrue(xmlfile is not None)
        index=0
        starttime=time.time()
        if self.debug:
            showProgressAt=500000
        else:
            showProgressAt=5000000
        for _, elem in dblp.iterParser():
            index+=1
            if index%showProgressAt==0:
                elapsed=time.time()-starttime
                print ("%8d: %5.1f s %5.0f/s %s" % (index,elapsed,index/elapsed,elem))
            dblp.clear_element(elem)    
        self.assertTrue(index>70000000)
        
    def testAsDictOfLod(self):
        '''
        get  dict of list of dicts (tables)
        '''
        dblp=Dblp(dtd_validation=False)
        xmlfile=dblp.getXmlFile()
        self.assertTrue(xmlfile is not None)
        limit=1000000000
        sample=5
        starttime=time.time()
        dictOfLod=dblp.asDictOfLod(limit,progress=1000000)
        elapsed=time.time()-starttime
        for i, (kind, lod) in enumerate(dictOfLod.items()):
            print ("#%4d %5d: %s" % (i+1,len(lod),kind))
            for j,row in enumerate(lod):
                print ("  %4d: %s" % (j,row)) 
                if j>sample:
                    break
        print ("%5.1f s %5d rows/s" % (elapsed,limit/elapsed))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
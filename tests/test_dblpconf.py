'''
Created on 2021-01-25

@author: wf
'''
import unittest
from dblpconf.dblp import Dblp
import os
import time
from lodstorage.sql import SQLDB, EntityInfo

class TestDblpConf(unittest.TestCase):
    '''
    test the dblp conferences access
    '''

    def setUp(self):
        self.debug=True
        self.mock=True
        pass

    def tearDown(self):
        pass
    
    def getDlp(self):
        '''
        get the dblp xml file
        '''
        dblp=Dblp()
        if self.mock:
            dblp.xmlpath="/tmp/dblp"
            dblp.gzurl="http://wiki.bitplan.com/images/confident/dblp.xml.gz"
            dblp.reinit()
        self.xmlfile=dblp.getXmlFile()
        if self.debug:
            print("dblp xml file is %s " % self.xmlfile)
        return dblp
    
    def testDblpConf(self):
        '''
        test dblp access
        '''
        dblp=self.getDlp()
        minsize=988816 if self.mock else 3099271450
        self.assertTrue(dblp.isDownloaded(minsize=minsize))
        pass
    
    def testParser(self):
        '''
        test parsing the xml file
        '''
        dblp=self.getDlp()
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
        expectedIndex=35000 if self.mock else 70000000
        self.assertTrue(index>expectedIndex)
        
    def testAsDictOfLod(self):
        '''
        get  dict of list of dicts (tables)
        '''
        dblp=self.getDlp()
        xmlfile=dblp.getXmlFile()
        self.assertTrue(xmlfile is not None)
        limit=10000
        sample=5
        starttime=time.time()
        dictOfLod=dblp.asDictOfLod(limit,progress=1000)
        elapsed=time.time()-starttime
        xmlpath="/tmp/dblp"
        os.makedirs(xmlpath,exist_ok=True)
        dbname="%s/%s" % (xmlpath,"dblp.sqlite")
        if os.path.isfile(dbname):
            os.remove(dbname)
        executeMany=True;
        fixNone=True
        sqlDB=SQLDB(dbname=dbname,debug=self.debug,errorDebug=True)
        for i, (kind, lod) in enumerate(dictOfLod.items()):
            print ("#%4d %5d: %s" % (i+1,len(lod),kind))
            entityInfo=sqlDB.createTable(lod[:100],kind,'key')
            sqlDB.store(lod,entityInfo,executeMany=executeMany,fixNone=fixNone)
            for j,row in enumerate(lod):
                print ("  %4d: %s" % (j,row)) 
                if j>sample:
                    break
        print ("%5.1f s %5d rows/s" % (elapsed,limit/elapsed))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
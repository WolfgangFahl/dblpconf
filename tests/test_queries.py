'''
Created on 2021-01-31

@author: wf
'''
import unittest
import os
from lodstorage.query import QueryManager
from lodstorage.sparql import SPARQL

class TestQueries(unittest.TestCase):
    '''
    test the pre packaged queries
    '''

    def setUp(self):
        self.debug=False
        pass


    def tearDown(self):
        pass


    def testQueries(self):
        '''
        test the queries
        '''
        path="%s/../queries" % os.path.dirname(__file__)
        qm=QueryManager(lang='sparql',debug=False,path=path)
        self.assertEqual(1,len(qm.queriesByName)) 
        endpoint="http://jena.zeus.bitplan.com/wikidata"
        endpoint="https://query.wikidata.org/sparql"
        sparql=SPARQL(endpoint)
        for name,query in qm.queriesByName.items():
            #print(query.query)
            listOfDicts=sparql.queryAsListOfDicts(query.query)
            markup=query.asWikiMarkup(listOfDicts)
            if self.debug:
                print("== %s ==" % (name))
                print("=== query ===")
                print (query.asWikiSourceMarkup())
                print("=== result ===")
                print(markup)
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
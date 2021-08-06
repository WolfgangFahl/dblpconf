'''
Created on 2021-01-26

@author: wf
'''
import unittest
from ormigrate.toolbox import HelperFunctions as hf
from dblp.webserver import WebServer
from datasources.dblpxml import DblpXml
import os.path
import datetime
import getpass
import csv
from corpus.lookup import CorpusLookup
from tests.testSMW import TestSMW

class TestWebServer(unittest.TestCase):
    '''
    Test the dblpconf web server
    '''

    @classmethod
    def setUpClass(cls):
        '''
        test the webserver
        ''' 
        cls.debug=False
        sourceWikiId='orclone'
        targetWikiId='myor'
        mock=True
        cls.web=WebServer()
        app=cls.web.app
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        cls.app = app.test_client()
        # https://stackoverflow.com/questions/44417552/working-outside-of-application-context-flaskclient-object-has-no-attribute-app
        cls.web.init(sourceWikiId, targetWikiId,cls.configureCorpusLookup)
        pass

    @staticmethod
    def getMockedDblp(mock=True, debug=False):
        dblpXml = DblpXml(debug=debug)
        if mock:
            dblpXml.xmlpath = "/tmp/dblp"
            dblpXml.gzurl = "https://github.com/WolfgangFahl/ConferenceCorpus/wiki/data/dblpsample.xml.gz"
            dblpXml.reinit()
        xmlfile = dblpXml.getXmlFile()
        if debug:
            print("dblp xml file is  %s with size %5.1f MB" % (xmlfile, dblpXml.getSize() / 1024 / 1024))
        return dblpXml

    @classmethod
    def configureCorpusLookup(cls, lookup:CorpusLookup):
        '''
        callback to configure the corpus lookup
        '''
        print("configureCorpusLookup callback called")
        dblpDataSource = lookup.getDataSource("dblp")
        dblpXml = cls.getMockedDblp(debug=cls.debug)
        dblpDataSource.eventManager.dblpXml = dblpXml
        dblpDataSource.eventSeriesManager.dblpXml = dblpXml
        for lookupId in ["orclone"]:
            wikiUser = TestSMW.getSMW_WikiUser(lookupId, save=True)
            orDataSource = lookup.getDataSource(f'{lookupId}')
            wikiFileManager = TestSMW.getWikiFileManager(wikiId=lookupId)
            orDataSource.eventManager.wikiFileManager = wikiFileManager
            orDataSource.eventSeriesManager.wikiFileManager = wikiFileManager
            orDataSource = lookup.getDataSource(lookupId)
            orDataSource.eventManager.wikiUser = wikiUser
            orDataSource.eventSeriesManager.wikiUser = wikiUser

        # wikiuser=TestSMW.getWikiUser()
        pass


    def setUp(self):
        self.debug=TestWebServer.debug
        self.app=TestWebServer.app
        self.web=TestWebServer.web
    
    def getResponse(self,query:str):
        '''
        get a response from the app for the given query string
        
        Args:
            query(str): the html query string to fetch the response for
        '''
        response=self.app.get(query)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data is not None)
        html=response.data.decode()
        if self.debug:
            print(html)
        return html

    def tearDown(self):
        pass

    def testDblpEventDataSource(self):
        '''
        test the samples handling
        '''
        html=self.getResponse("/cc/dblp/Event/100")
        self.assertTrue("> publicationSeries </th>" in html)
        pass

    def testOREvents(self):
        '''
        test OPEN RESEARCH event list
        '''
        html=self.getResponse("/openresearch/Event")
        self.assertTrue("acronym" in html)
        pass

    def testCsvDownload(self):
        '''
        test OPENSRESEARCH csv generation
        '''
        eventFile = self.getResponse("/openresearch/Event/3DUI 2016/download")
        self.assertIsNotNone(eventFile)
        eventSeriesFile = self.getResponse("/openresearch/EventSeries/3DUI/download")
        self.assertIsNotNone(eventSeriesFile)
        pass

    def testORCountries(self):
        '''
        test OPENSRESEARCH event list
        '''
        if getpass.getuser()!="wf":
            return
        html=self.getResponse("/openresearch/Country")
        self.assertTrue("wikidataId" in html)
        pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
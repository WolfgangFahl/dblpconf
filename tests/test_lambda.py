'''
Created on 2021-01-23

@author: wf
'''
import unittest
from wikibot.wikiuser import WikiUser
from wikibot.wikiclient import WikiClient
from wikibot.smw import SMWClient

class TestLambda(unittest.TestCase):
    '''
    test lamdba query/action handling
    '''

    def setUp(self):
        self.debug=True
        pass


    def tearDown(self):
        pass


    def testLambda(self):
        '''
        test the lamdba handling
        '''
        wusers=WikiUser.getWikiUsers()
        if 'test' in wusers:
            wuser=wusers['test']
            if wuser.url=="http://test.bitplan.com":
                ask="""{{#ask: [[Concept:Sourcecode]]
|mainlabel=Sourcecode
| ?Sourcecode id = id
| ?Sourcecode lang = lang
| ?Sourcecode author = author
| ?Sourcecode since = since
| ?Sourcecode text = text
| ?Sourcecode url = url
}}"""
                wikiclient=WikiClient.ofWikiUser(wuser)
                smw=SMWClient(wikiclient.getSite())
                result=smw.query(ask)
                if self.debug:
                    print (len(result))
                    print (result)  
                self.assertTrue('WikiDataConferenceSeriesSparqlQuery' in result)
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
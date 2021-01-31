'''
Created on 2021-01-23

@author: wf
'''
import unittest
from wikibot.wikiuser import WikiUser
from wikibot.wikiclient import WikiClient
from wikibot.smw import SMWClient
from lodstorage.query import Query
from action.lambda_action import Code, LambdaAction
import tests.test_dblp 

class TestLambda(unittest.TestCase):
    '''
    test lamdba query/action handling
    '''

    def setUp(self):
        self.debug=False
        self.dblp=tests.test_dblp.TestDblp.getMockedDblp()
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
                qid= 'DblpConfSeriesQuery'
                self.assertTrue(qid in result)
                qCode=result[qid]
                query=Query(name=qCode['id'],query=qCode['text'],lang=qCode['lang'])
                sid='EchoCode'
                sCode=result[sid]
                self.assertTrue(sid in result)
                code=Code(name=sCode['id'],text=sCode['text'],lang=sCode['lang'])
                action=LambdaAction("testLambdaAction",query=query,code=code)
                sqlDB=self.dblp.getSqlDB(postProcess=self.dblp.postProcess)
                action.execute(sqlDB)
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
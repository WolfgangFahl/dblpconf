'''
Created on 2021-01-23

@author: wf
'''
import unittest
from wikibot.wikiuser import WikiUser
from wikibot.wikiclient import WikiClient
from wikibot.smw import SMWClient
from action.wikiaction import WikiAction
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
                wikiclient=WikiClient.ofWikiUser(wuser)
                smw=SMWClient(wikiclient.getSite())
                wikiAction=WikiAction(smw)
                lambdaAction=wikiAction.getLambdaAction('test action','DblpConfSeriesQuery','EchoCode')
                sqlDB=self.dblp.getSqlDB(postProcess=self.dblp.postProcess)
                context={"sqlDB": sqlDB,"smw":smw}
                lambdaAction.execute(context=context)
                self.assertTrue('result' in context)
                result=context['result']
                self.assertTrue('message' in result)
                message=result["message"]
                self.debug=True
                if self.debug:
                    print(message)
                self.assertTrue("printed" in message)
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
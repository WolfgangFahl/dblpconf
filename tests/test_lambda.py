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
    
    def getSMW(self,wikiId='test',url='http://test.bitplan.com'):
        smw=None
        wikiclient=None
        wusers=WikiUser.getWikiUsers()
        if 'test' in wusers:
            wuser=wusers['test']
            if wuser.url=="http://test.bitplan.com":
                wikiclient=WikiClient.ofWikiUser(wuser)
                smw=SMWClient(wikiclient.getSite())
        return smw,wikiclient
    
    def testLambda(self):
        '''
        test the lamdba handling
        '''
        smw,wikiclient=self.getSMW()
        if smw is not None:
            wikiAction=WikiAction(smw)
            lambdaAction=wikiAction.getLambdaAction('test action','DblpConfSeriesQuery','EchoCode')
            sqlDB=self.dblp.getSqlDB(postProcess=self.dblp.postProcess)
            context={"sqlDB": sqlDB,"smw":smw}
            lambdaAction.execute(context=context)
            message=lambdaAction.getMessage(context)
            if self.debug:
                print(message)
            self.assertTrue(message is not None)
            self.assertTrue("printed" in message)
        pass
    
    def testPlayGround(self):
        return
        smw,wikiclient=self.getSMW()
        if smw is not None:
            wikiAction=WikiAction(smw)
            lambdaAction=wikiAction.getLambdaAction('test action','DblpConfSeriesQuery','DblpImport')
            sqlDB=self.dblp.getSqlDB(postProcess=self.dblp.postProcess)
            context={"sqlDB": sqlDB,"smw":smw,"wikiclient":wikiclient}
            wikiclient.login()
            lambdaAction.executeQuery(context)
            self.dblpImport(context)
            message=lambdaAction.getMessage(context)
            print(message)
    
        
    def dblpImport(self,context):
        # this is a lambda Action action
        # it get's its context from a context dict
        rows=context["rows"]
        wikiclient=context["wikiclient"]
        rows=rows[:10]
        existCount=0
        importCount=0
        for row in rows:
            pageContent="""{{EventSeries
|Acronym=%s
|Title=%s
}}""" % (row["conf"],row["title"])
            pageTitle=row["conf"]
            page=wikiclient.getPage(pageTitle)
            importCount+=1;
            if page.exists:
                existCount+=1
            comment='imported by dblpimport'
            page.edit(pageContent,comment)    
            
        context["result"]={"message":"%d/%d event series imported (%d existed)" %(importCount,len(rows),existCount)}    


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
'''
Created on 2021-01-26

@author: wf
'''
import unittest
from dblp.webserver import WebServer
from tests.test_dblp import TestDblp

class TestWebServer(unittest.TestCase):

    def setUp(self):
        '''
        test the webserver
        ''' 
        self.debug=True
        mock=True
        _,dblp=TestDblp.getMockedDblp(mock, debug=self.debug)
        web=WebServer(dblp)
        app=web.app
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        self.app = app.test_client()
        pass
    
    def getResponse(self,query):
        response=self.app.get(query)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data is not None)
        html=response.data.decode()
        if self.debug:
            print(html)
        return html

    def tearDown(self):
        pass

    def testSamples(self):
        html=self.getResponse("/sample/article/100")
        self.assertTrue("<th> publtype </th>" in html)
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
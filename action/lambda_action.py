'''
Created on 31.01.2021

@author: wf
'''
from lodstorage.query import Query

class Code(object):
    '''
    a piece of code
    '''
    
    def __init__(self, name:str,text:str,lang:str='python'):
        '''
        construct me from the given text and language
        '''
        self.name=name
        self.text=text
        self.lang=lang
        
    def execute(self,x):
        '''
        https://stackoverflow.com/questions/701802/how-do-i-execute-a-string-containing-python-code-in-python
        https://stackoverflow.com/questions/436198/what-is-an-alternative-to-execfile-in-python-3
        https://stackoverflow.com/questions/2220699/whats-the-difference-between-eval-exec-and-compile
        '''
        exec(self.text)
        pass

class LambdaAction(object):
    '''
    a lambda action
    '''

    def __init__(self, name:str,query:Query,code:Code):
        '''
        Constructor
        '''
        self.name=name
        self.query=query
        self.code=code
        
    def execute(self,db):
        '''
        run my query and feed the result into the given code
        '''
        lod=db.query(self.query.query)
        for row in lod:
            self.code.execute(str(row))
        pass
        


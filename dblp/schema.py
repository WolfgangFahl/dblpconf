'''
Created on 2021-01-26

@author: wf
'''

class SchemaManager(object):
    def __init__(self,baseUrl="http://wiki.bitplan.com/index.php/Dblpconf#"):
        self.baseUrl=baseUrl
        self.schemasByName={}
        schemaDefs={
                'article': 'Article',
                'book':'Book',
                'incollection': 'In Collection',
                'inproceedings': 'In Proceedings',
                'mastersthesis': 'Master Thesis',
                'phdthesis': "PhD Thesis",
                'proceedings':'Proceedings',
                'www':'Person'
            }
        for key,name in schemaDefs.items():
            self.schemasByName[key]=Schema(key,name) 
        pass
 
class Schema(object):
    '''
    classdocs
    '''


    def __init__(self,name,title):
        '''
        Constructor
        '''
        self.name=name
        self.title=title
        self.propsByName={}
        
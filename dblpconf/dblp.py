'''
Created on 2021-01-25

@author: wf
'''
from pathlib import Path
from io import BytesIO
import os
import urllib.request
from gzip import GzipFile

class Dblp(object):
    '''
    handler for https://dblp.uni-trier.de/xml/ dumps
    '''

    def __init__(self,xmlname="dblp.xml",xmlpath=None,gzurl="https://dblp.uni-trier.de/xml/dblp.xml.gz"):
        '''
        Constructor
        
        Args:
            xmlfile: name of the xml file
            xmlpath: download path
            gzurl: url of the gzipped original file
        '''
        if xmlpath is None:
            home = str(Path.home())
            xmlpath="%s/.dblp" % home
        self.gzurl=gzurl
        self.xmlname=xmlname
        self.xmlpath=xmlpath
        self.xmlfile="%s/%s" % (self.xmlpath,self.xmlname)
        
    def getXmlFile(self):
        '''
        get the dblp xml file - will download the file if it doesn't exist
        
        Returns:
            str: the xmlfile
        '''
        if not os.path.isfile(self.xmlfile):
            os.makedirs(self.xmlpath,exist_ok=True)
            urlreq = urllib.request.urlopen(self.gzurl)
            z = GzipFile(fileobj=BytesIO(urlreq.read()), mode='rb')
            with open(self.xmlfile, 'wb') as outfile:
                outfile.write(z.read())
        return self.xmlfile
                
            
            
        
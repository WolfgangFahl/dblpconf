'''
Created on 2021-01-25

@author: wf
'''
from pathlib import Path
from io import BytesIO
import os
import urllib.request
from gzip import GzipFile
from lxml import etree

class Dblp(object):
    '''
    handler for https://dblp.uni-trier.de/xml/ dumps
    see https://github.com/IsaacChanghau/DBLPParser/blob/master/src/dblp_parser.py
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
        self.dtdfile="%s/%s" % (self.xmlpath,self.xmlname.replace(".xml",".dtd"))
        
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
        if not os.path.isfile(self.dtdfile):
            dtdurl=self.gzurl.replace(".xml.gz",".dtd")
            urllib.request.urlretrieve (dtdurl, self.dtdfile)
        
        return self.xmlfile
    
    def iterParser(self):
        """
           Create a dblp data iterator of (event, element) pairs for processing
           Returns:
               etree.iterparse result
        """
        if not os.path.isfile(self.xmlfile):
            raise ("dblp xml file %s not downloaded yet - please call getXmlFile first")
        # with dtd validation
        return etree.iterparse(source=self.xmlfile, events=('end', 'start' ), dtd_validation=True, load_dtd=True)  
    
    def clear_element(self,element):
        """Free up memory for temporary element tree after processing the element"""
        element.clear()
        while element.getprevious() is not None:
            del element.getparent()[0]
    
    def asDictOfLod(self,limit=1000):
        '''
        get the dblp data as a list of dicts
        '''
        index=0
        level=0
        dictOfLod={}
        current={}
        for event, elem in self.iterParser():
            if event == 'start': 
                level += 1;
                if level==2:
                    kind=elem.tag
                    if not kind in dictOfLod:
                        dictOfLod[kind]=[]
                    lod=dictOfLod[kind]
                elif level==3:
                    current[elem.tag]=elem.text    
            elif event == 'end':
                if level==2:
                    lod.append(current)
                    current={} 
                level -= 1;
            index+=1
            self.clear_element(elem)
            if index>=limit:
                break
        return dictOfLod
            
        
    
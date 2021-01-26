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

    def __init__(self,xmlname:str="dblp.xml",dtd_validation:bool=False,xmlpath:str=None,gzurl:str="https://dblp.uni-trier.de/xml/dblp.xml.gz"):
        '''
        Constructor
        
        Args:
            xmlname (str): name of the xml file
            dtd_validation (bool): True if dtd validation should be activated when parsing
            xmlpath(str): download path
            gzurl(str): url of the gzipped original file
        '''
        if xmlpath is None:
            home = str(Path.home())
            xmlpath="%s/.dblp" % home
        self.gzurl=gzurl
        self.xmlname=xmlname
        self.xmlpath=xmlpath
        self.dtd_validation=dtd_validation
        self.reinit()
        
    def reinit(self):
        '''
        reinitialize my file names
        '''
        self.xmlfile="%s/%s" % (self.xmlpath,self.xmlname)
        self.dtdfile="%s/%s" % (self.xmlpath,self.xmlname.replace(".xml",".dtd"))
        
    def isDownloaded(self,minsize:int=3000000000)->bool:
        '''
        check that the dblp file is downloaded
        
        Returns:
            bool: True if the dblpfile is fully downloaded and is bigger than the given minimum size
        '''
        result=os.path.isfile(self.xmlfile)
        if result:
            stats=os.stat(self.xmlfile)
            result=stats.st_size>=minsize
        return result
        
        
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
        return etree.iterparse(source=self.xmlfile, events=('end', 'start' ), dtd_validation=self.dtd_validation, load_dtd=True)  
    
    def clear_element(self,element):
        """
        Free up memory for temporary element tree after processing the element
        
            Args:
                element(node): the etree element to clear together with it's parent
        """
        element.clear()
        while element.getprevious() is not None:
            del element.getparent()[0]
            
            
    def asDictOfLod(self,limit:int=1000,delim:str=',',progress:int=None):
        '''
        get the dblp data as a dict of list of dicts - effectively separating the content
        into table structures
        
        Args:
            limit(int): maximum amount of records to process
            delim(str): the delimiter to use for splitting attributes with multiple values (e.g. author)
            progress(int): if set the interval at which to print a progress dot 
        '''
        index=0
        count=0
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
                    if hasattr(elem, "attrib"):
                        current = {**current, **elem.attrib}
                elif level==3:
                    if elem.tag in current:
                        current[elem.tag]="%s%s%s" % (current[elem.tag],delim,elem.text)
                    else:
                        current[elem.tag]=elem.text    
            elif event == 'end':
                if level==2:
                    lod.append(current)
                    count+=1
                    current={} 
                    if progress is not None:
                        if count%progress==0:
                            print(".",flush=True,end='')
                        if count%(progress*80)==0:
                            print("\n",flush=True)
                    if count>=limit:
                        break
                level -= 1;
            index+=1
            self.clear_element(elem)
        return dictOfLod
            
        
    
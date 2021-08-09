'''
Created on 2020-12-30

@author: wf
'''
from functools import partial
from os.path import expanduser

from corpus.eventcorpus import EventDataSource
from fb4.app import AppWrap
from fb4.login_bp import LoginBluePrint
from fb4.sqldb import db
from fb4.widgets import Link, MenuItem, DropDownMenu, Widget
from flask import abort,flash,render_template, url_for,send_file,request,redirect
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from lodstorage.csv import CSV
from lodstorage.sql import SQLDB
from lodstorage.storageconfig import StorageConfig
from corpus.lookup import CorpusLookup, CorpusLookupConfigure
from ormigrate.smw.rating import Rating
from wikifile.wikiFileManager import WikiFileManager

import os
import json


from wikibot.wikiuser import WikiUser
from wikibot.wikiclient import WikiClient
from wikibot.smw import SMW,SMWClient
from wtforms import HiddenField, SubmitField, StringField, SelectField
from ormigrate.toolbox import HelperFunctions as hf
from corpus.lookup import CorpusLookup

class WebServer(AppWrap):
    ''' 
    dblp conf webserver
    '''
    
    def __init__(self, host='0.0.0.0', port=8252, verbose=True,debug=False):
        '''
        constructor
        
        Args:
            host(str): flask host
            port(int): the port to use for http connections
            debug(bool): True if debugging should be switched on
            verbose(bool): True if verbose logging should be switched on
            dblp(Dblp): preconfigured dblp access (e.g. for mock testing)
        '''
        self.debug=debug
        self.verbose=verbose
        self.lookup=None
        scriptdir = os.path.dirname(os.path.abspath(__file__))
        template_folder=scriptdir + '/../templates'
        super().__init__(host=host,port=port,debug=debug,template_folder=template_folder)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.app_context().push()
        db.init_app(self.app)
        self.db=db
        self.loginBluePrint=LoginBluePrint(self.app,'login')
        
        #
        # setup global handlers
        #
        @self.app.before_first_request
        def before_first_request_func():
            loginMenuList=self.adminMenuList("Login")
            self.loginBluePrint.setLoginArgs(menuList=loginMenuList)
            
        @self.app.route('/')
        def index():
            return self.index()
        
        @self.app.route('/sample/<dbId>/<entity>/<int:limit>')
        def showSample(dbId,entity,limit):
            return self.showSample(dbId,entity,limit)

        @self.app.route('/cc/<dataSourceId>/<entity>/<int:limit>')
        def showEventBaseManager(dataSourceId, entity, limit):
            return self.showEventBaseManager(dataSourceId, entity, limit)
        
        @self.app.route('/series/<series>')
        def showSeries(series):
            return self.showSeries(series)
        
        @self.app.route('/wikidata/<entity>')
        def showWikiData(entity:str):
            return self.showWikiData(entity)
        
        @self.app.route('/openresearch/<entity>/<pagename>',methods=['GET', 'POST'])
        def showOpenResearchPage(entity,pagename):
            return self.showOpenResearchPage(entity,pagename)

        @login_required
        @self.app.route('/openresearch/upload/', methods=['GET', 'POST'])
        def getCsvFromUser():
            return self.getCsvFromUser()

        @login_required
        @self.app.route('/openresearch/<entity>',methods=['GET', 'POST'])
        def showOpenResearchData(entity):
            return self.showOpenResearchData(entity)

        @self.app.route('/openresearch/<entity>/<pagename>/download', methods=['GET', 'POST'])
        def downloadCsv(entity,pagename):
            return self.downloadCsv(entity,pagename)

        @login_required
        @self.app.route('/openresearch/updatecache', methods=['GET', 'POST'])
        def updateCache():
            return self.updateCache()
 
    def init(self,sourceWikiId,targetWikiId,corpusConfiguration=CorpusLookupConfigure.configureCorpusLookup):
        '''
        initialize me with the given sourceWikiId and targetWikiId
        '''
        self.initConferenceLookup(corpusConfiguration)
        self.sourceWikiId=sourceWikiId
        self.targetWikiId=targetWikiId
 

    
    def log(self,msg):
        '''
        log the given message
        '''
        if self.verbose:
            print(msg)


    def initConferenceLookup(self,corpusConfiguration=CorpusLookupConfigure.configureCorpusLookup):
        '''
        initialize the conference Lookup Corpus
        '''
        self.log("Initializing ConferenceLookup...")
        self.lookup=CorpusLookup(lookupIds=["orclone","orclone-backup", "dblp", "wikidata"], configure=corpusConfiguration)
        self.lookup.load()
        self.orDataSource = self.lookup.getDataSource("orclone-backup")
        self.dblpDataSource = self.lookup.getDataSource("dblp")
        self.wikidataDataSource=self.lookup.getDataSource("wikidata")
        if hasattr(self, 'dbInitialized') and self.dbInitialized:
            # TODO - refactor to
            pass
        self.dbInitialized=True
         

    def updateConferenceCorpus(self):
        '''
        update the conferenceCorpus
        '''
        # TODO - do not implement in beginning of August 2021
        # other functions have priority
        wikiId = self.getWikiIdForLoggedInUser()
        wikiUser = hf.getSMW_WikiUser(wikiId)
        self.log(f"Updating cache from {wikiId}")
        
        return self.showOpenResearchData('Event')
        
    def getUserNameForWikiUser(self,wuser:WikiUser)->str:
        '''
        get the username for the given wiki user
        
        Args:
            wuser(WikiUser): the user to get the username for
        
        Returns:
            str: a fully qualifying username e.g. testuser@testwiki
        '''
        username="%s@%s" % (wuser.user,wuser.wikiId)
        return username
        
    def initUsers(self):
        '''
        initialize my users
        '''  
        wusers=WikiUser.getWikiUsers()
        self.log(f"Initializing {len(wusers)} users ...")
        for userid,wuser in enumerate(wusers.values()):
            username=self.getUserNameForWikiUser(wuser)
            self.loginBluePrint.addUser(self.db,username,wuser.getPassword(),userid=userid)
        
    def linkColumn(self,name,record,formatWith=None,formatTitleWith=None):
        '''
        replace the column with the given name with a link
        '''
        if name in record:
            value=record[name]
            if value is None:
                record[name]=''
            else:
                if formatWith is None:
                    lurl=value
                else:
                    lurl=formatWith % value
                if formatTitleWith is None:
                    title=value
                else:
                    title=formatTitleWith % value
                record[name]=Link(lurl,title)
        
    def linkRecord(self,record):
        '''
        link the given record
        '''
        self.linkColumn("ee", record)
        self.linkColumn("url",record,formatWith="https://dblp.org/%s")
        if 'conf' in record:
            conf=record['conf']
            value=Link(self.basedUrl(url_for("showSeries",series=conf)),conf) if conf is not None else ""
            record['conf']=value
         
    def showSeries(self,key):
        '''
        return the series for the given key
        '''
        query="select * from proceedings where conf=? order by year desc"
        records=self.sqlDB.query(query,(key,))
        for record in records:
            self.linkRecord(record)
                
        menuList=self.adminMenuList("Home")
        html=render_template("sample.html",title=key,menuList=menuList,dictList=records)
        return html
    
    def showWikiData(self, entity):
        '''
        show the list of wikidata entries
        '''
        # TODO make live/cache configurable
        # live query or cache? → cache query takes around 20s
        listOfDicts=[]
        if entity == 'EventSeries':
            records=self.wikidataDataSource.eventSeriesManager.getList()
            listOfDicts=[vars(d).copy() for d in records]
            for row in listOfDicts:
                row['confSeries']=Link(row['confSeries'],row['acronym'])
                if 'DBLP_pid' in row:
                    conf=row['DBLP_pid']
                    if conf is None:
                        row['DBLP_pid']=""
                        row['conf']=''
                    else:
                        conf=conf.replace("conf/","")
                        self.linkColumn('DBLP_pid',row, formatWith="https://dblp.org/db/%s")
                        row['conf']=Link(self.basedUrl(url_for("showSeries",series=conf)),conf)
                self.linkColumn('WikiCFP_pid',row,formatWith="http://www.wikicfp.com/cfp/program?id=%s",formatTitleWith="wikicfp %s")
                self.linkColumn("Microsoft_Academic_pid",row,formatWith="https://academic.microsoft.com/conference/%s")
                self.linkColumn("Publons_pid",row,formatWith="https://publons.com/journal/%s")
                self.linkColumn("FreeBase_pid",row,formatWith="https://freebase.toolforge.org/%s")
                self.linkColumn("ACM_pid",row,formatWith="https://dl.acm.org/conference/%s")
                self.linkColumn('GND_pid', row, formatWith="https://lobid.org/gnd/%s")
                self.linkColumn("official_website", row)
        elif entity == "Event":
            records = self.wikidataDataSource.eventManager.getList()
            listOfDicts = [vars(d).copy() for d in records]
            for row in listOfDicts:
                self.linkColumn('eventId', row)
                self.linkColumn('eventInSeriesId', row)
                self.linkColumn('homepage', row)
                self.linkColumn('countryId', row)
        else:
            abort(404)
        menuList=self.adminMenuList("wikidata")
        html=render_template("sample.html",title="wikidata",menuList=menuList,dictList=listOfDicts)
        return html
    
    def convertToLink(self,record:dict,field:str,formatStr:str):
        '''
        convert the field in the given record to a Link using the given formatStr
        
        Args:
            record(dict): the record to work on
            field(str): the name of the field
            formatStr(str): the format string to use
        '''
        if field in record:
            value=record[field]
            url=formatStr % value
            record[field]=Link(url,value)

    def removeRecordFields(self, record:dict,fields:list):
        '''Removes the given list of fields form the given record
        Args:
            record(dict): the record to work on
            fields(list): list of fields that should be removed from the record
        '''
        for field in fields:
            if field in record:
                del record[field]
                
    def showOpenResearchPage(self,entityName:str,pageName:str):
        '''
        show the given instance of the entity with the given pagenName
        '''
        menuList = self.adminMenuList("OpenResearch")
        # TODO Decide which wikiUser to use e.g.
        eventManager=self.orDataSource.eventManager
        if hasattr(eventManager, 'wikiUser'):
            wikiUser=eventManager.wikiUser
        else:
            wikiUser=eventManager.wikiFileManager.wikiUser
        wikiclient=WikiClient.ofWikiUser(wikiUser)
        content=wikiclient.getHtml(pageName)
        title=f"entity: {entityName} pageName: {pageName} url for wikiuser: {wikiUser.getWikiUrl()}"
        downloadLink=f"/openresearch/EventSeries/{pageName}/download"
        return render_template("orpage.html",title=title,content=content,menuList=menuList, downloadLink=downloadLink)
        
    def fixPageTitle(self,pageTitle:str):
        '''
        fix the given pageTitle
        
        Args:
            pageTitle(str): a MediaWiki pageTitle
            
        Return:
            a fixed version 
        '''
        result=pageTitle.replace(" ","_")
        return result

    def ensureDirectoryExists(self,file_path:str):
        '''
        check that the given path exists and otherwise create it
        
        Args
            file_path(str): the path to check
        '''
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)


    def downloadCsv(self, entityname, pagename):
        '''
        Function to send the csv file to the webpage for the user to download
        
        Args:
            entityname(str): the entityName to download
            pagename(str): the page for which to start the download
        '''
        # ToDo align to ConferenceCorpus interface
        csvString=''
        if entityname == 'Event':
            #filepath=self.OREventCorpus.getEventCsv(pagename)
            pass
        elif entityname == 'EventSeries':
            eventManager=self.orDataSource.eventManager
            csvString=eventManager.asCsv(selectorCallback=partial(eventManager.getEventsInSeries, pagename))
        # ToDo: write csvString to temp file for download
        filepath=f"{expanduser('~')}/.ptp/csvs/{pagename}.csv"
        CSV.writeFile(csvString, filepath)
        if self.debug:
            print(filepath)
        return send_file(filepath, as_attachment=True,max_age=0)
        

    def getCsvFromUser(self):
        '''
        Function to get csv from user and push to wiki
        '''
        if request.method == "POST":
            if request.files:
                csv = request.files["csv"]
                # TODO: Process file to wikiFile using OREventCorpus
                wikiURL=self.getWikiURLForLoggedInUser()
                return redirect(wikiURL)
        menuList = self.adminMenuList("OpenResearch")
        html = render_template('upload.html',menuList=menuList)
        return html

    def showOpenResearchData(self, entityName:str):
        '''
        show the list of all events available in OPENRESEARCH
        Args:
            entityName: Show the data of the given entity. If the entity is not known redirect to home page and show error message
            limit: Upper limit of the data to be shown
        '''
        #Assumption data for entites is always converted to LOD to render it as table
        limit=100
        menuList = self.adminMenuList("OpenResearch")

        rating=None
        #ToDo Get Event ratings
        orDataSource=self.lookup.getDataSource("orclone-backup")
        if entityName == "Event":
            #rating=Event.rateMigration
            eventManager=orDataSource.eventManager
            lod=eventManager.getList()
        if entityName == "EventSeries":
            #rating=EventSeries.rateMigration
            eventSeriesManager=orDataSource.eventSeriesManager
            lod=eventSeriesManager.getList()
        lod = [vars(d).copy() for d in lod]
        #TODO - add rating again (later)
        #if len(errors)>0:
        #    errorMsg = f"{len(errors)} rating processing errors"
        #    print(errorMsg)
        #    flash(message=errorMsg, category="warning")

        for record in lod:
            if not current_user.is_authenticated:
                # Remove record fields that should only be visable for users with login rights
                loginRequiredFields = ["lastEditor"]
                self.removeRecordFields(record,loginRequiredFields)
            if 'pageTitle' in record:
                record['orpage']=self.fixPageTitle(record['pageTitle'])
                self.convertToLink(record,'orpage',f"/openresearch/{entityName}/%s")
            #self.convertToLink(record, 'pageTitle', f"{wikiurl}/%s")
            self.convertToLink(record, 'wikidataId', "https://www.wikidata.org/wiki/%s")
            self.convertToLink(record, 'dblpSeries', "https://dblp.org/db/conf/%s/index.html")
            if "lastEditor" in record:
                record["lastEditor"]=record["lastEditor"].replace("User:","")
            self.convertToLink(record, 'lastEditor',"https://www.openresearch.org/wiki/Special:Contributions/%s")
            if isinstance(record,dict):
                for column in record.keys():
                    value=record.get(column)
                    # if isinstance(value,Rating):
                    #     record[column]=RatingWidget(value)
            else:
                print(record) # what?
        lodKeys = self.get_prop_list_from_samples(lod)
        lodKeys =["orpage"] + lodKeys
        tableHeaders = [x.replace("PainRating", "\nPainRating") for x in lodKeys]   # FIXME: Easy hack for the time being
        return render_template('sample.html',title=entityName,menuList=menuList, dictList=lod, lodKeys=lodKeys, tableHeaders=tableHeaders)

    @staticmethod
    def get_prop_list_from_samples(samples: list):
        """
        Returns a list of used keys by the given list of dicts
        """
        if samples is None:
            return None
        prop_list = []
        for sample in samples:
            for key in sample.keys():
                if key not in prop_list:
                    prop_list.append(key)
        return prop_list

    def getSMWForLoggedInUser(self):
        wusers=WikiUser.getWikiUsers()
        luser=self.loginBluePrint.getLoggedInUser()
        smw=None
        wuser=None
        wikiclient=None
        for wuser in wusers.values():
            username=self.getUserNameForWikiUser(wuser)
            if luser.username==username:
                wikiclient=WikiClient.ofWikiUser(wuser)
                smw=SMWClient(wikiclient.getSite())
                break
        return wuser,wikiclient,smw

    def getWikiIdForLoggedInUser(self):
        '''
        Returns the wikiID of the loggedin user
        e.g. bob@myor is logged in then myor is retured
        '''
        wikiUser, wikiclient, smw = self.getSMWForLoggedInUser()
        wikiId = wikiUser.wikiId
        return wikiId

    def getWikiURLForLoggedInUser(self):
        '''
        Returns the wiki URL of the loggedin user
        e.g. bob@myor is logged in then returns the url for the myor wiki (defined in the .ini file)
        '''
        wikiUser, wikiclient, smw = self.getSMWForLoggedInUser()
        wikiURL=wikiUser.getWikiUrl()
        return wikiURL
        
    def showLambdaActions(self):
        '''
        show the available lambda Actions
        '''
        if not current_user.is_authenticated:
            abort(404)
        wuser,wikiclient,smw=self.getSMWForLoggedInUser()
        if smw is None:
            abort(404)
        else:
            return self.showLambdaActionsForSMW(smw,wuser)
        
    def getJsonColumn(self,form,field:str,col:int):
        '''
        get a column from a record transmitted via json in the given field of the given form at the given column
        
        example: 
        
        Args:
            form: the wtform posted
            field(str): the name of the (hidden) field that contains the json data
            col(int): the column index to get the data from
            
        Returns:
            str: the column content
        '''
        result=None
        if field in form:
            jsonText=form.data[field]
            row = json.loads(jsonText)
            if isinstance(row,list) and col<len(row):
                result=row[col]
                pass
        return result     
    
             
    def showSample(self,dbId:str,entity:str,limit:int):
        '''
        Args:
            dbId(str): id of the database either 'dblp' or 'ptp'
            entity(str): the name of the entity to show the samples for
            limit(int): how many elements to show as a sample
        
        Returns:
            str: the html code or aborts with a 404 if the entity is invalid or 501 if the limit is above 5000
        '''
        if not dbId in self.dbs:
            abort(404,"unknown dbId %s " % dbId)
        db=self.dbs[dbId]
        if (not entity in db.tableDict):
            abort(404)
        elif limit>5000:
            abort(501)
        else:
            menuList=self.adminMenuList(entity)

            samples=db.sqlDB.query("select * from %s limit %d" % (entity,limit))
            for record in samples:
                self.linkRecord(record)
            html=render_template("sample.html",title=entity,menuList=menuList,dictList=samples)
            return html

    def showEventBaseManager(self, dataSourceId:str, entity: str, limit: int):
        '''
        Args:
            dbId(str): id of the database either 'dblp' or 'ptp'
            entity(str): the name of the entity to show the samples for
            limit(int): how many elements to show as a sample

        Returns:
            str: the html code or aborts with a 404 if the entity is invalid or 501 if the limit is above 5000
        '''
        dataSource=self.lookup.getDataSource(lookupId=dataSourceId)
        if dataSource is None:
            abort(404, "unknown dataSourceId %s " % dataSourceId)
        if entity == "Event":
            records=dataSource.eventManager.getList()
        elif entity == "EventSeries":
            records=dataSource.eventSeriesManager.getList()
        if not records:
            abort(404)
        elif limit > 5000:
            abort(501)
        else:
            menuList = self.adminMenuList(entity)
            lod=[vars(d).copy() for d in records]
            for record in lod:
                self.linkRecord(record)
            html = render_template("sample.html", title=entity, menuList=menuList, dictList=lod)
            return html
            
    def adminMenuList(self,activeItem:str=None):
        '''
        get the list of menu items for the admin menu
        Args:
            activeItem(str): the active  menu item
        Return:
            list: the list of menu items
        '''
        menuList=[
            MenuItem(url_for('index'),'Home'),
            MenuItem('http://wiki.bitplan.com/index.php/Dblpconf','Docs'),
            MenuItem('https://github.com/WolfgangFahl/dblpconf','github'),
            ]
        # Add wikidata
        wikidataDropDownMenu = self.getDropDownMenuForEventDataSource('wikidata', self.wikidataDataSource, 'showWikiData')
        menuList.append(wikidataDropDownMenu)
        # Add dblp
        dblpDropDownMenu =self.getDropDownMenuForEventDataSource('dblp',self.dblpDataSource, 'showEventBaseManager')
        menuList.append(dblpDropDownMenu)
        # Add OPENRESEARCH
        orDropDownMenu=self.getDropDownMenuForEventDataSource('OPENRESEARCH',self.orDataSource, 'showOpenResearchData')
        menuList.append(orDropDownMenu)
        if current_user.is_anonymous:
            menuList.append(MenuItem('/login','login'))
        else:
            menuList.append(MenuItem('/logout','logout'))
        
        if activeItem is not None:
            for menuItem in menuList:
                if isinstance(menuItem,MenuItem):
                    if menuItem.title==activeItem:
                        menuItem.active=True
                    menuItem.url=self.basedUrl(menuItem.url)
        return menuList

    def getDropDownMenuForEventDataSource(self,name:str, dataSource:EventDataSource, pathCallback):
        dropDownMenu = DropDownMenu(name)
        for EntityList in [dataSource.eventManager,dataSource.eventSeriesManager]:
            entityName=EntityList.entityName
            pluralName=entityName
            url=url_for(pathCallback, entity=entityName, dataSourceId=dataSource.name, limit=1000)
            dropDownMenu.addItem(Link(self.basedUrl(url), pluralName))
        return dropDownMenu
    
    def index(self):
        '''
        show a conference overview
        '''
        menuList=self.adminMenuList("Home")
        # ToDo: Improve order of displayed list once the sql interface of ConferenceCorpus has improved
        confs=[vars(conf).copy() for conf in self.dblpDataSource.eventSeriesManager.getList()]
        html=render_template("sample.html",title="Event Series", dictList=confs,menuList=menuList)
        return html

class RatingWidget(Widget):
    '''
    Displays a rating
    '''

    def __init__(self, rating:Rating):
        super().__init__()
        self.rating = rating

    @staticmethod
    def lookupPainImage(rating: int):
        '''Returns html image tag to the corresponding pain rating'''
        painImages = {
             0: "http://rq.bitplan.com/images/rq/a/a3/Pain0.png",
             1: "https://rq.bitplan.com/images/rq/0/01/Pain1.png",
             2: "https://rq.bitplan.com/images/rq/0/01/Pain1.png",
             3: "https://rq.bitplan.com/images/rq/0/0a/Pain4.png",
             4: "https://rq.bitplan.com/images/rq/0/0a/Pain4.png",
             5: "https://rq.bitplan.com/images/rq/b/b0/Pain6.png",
             6: "https://rq.bitplan.com/images/rq/b/b0/Pain6.png",
             7: "https://rq.bitplan.com/images/rq/6/6c/Pain7.png",
             8: "https://rq.bitplan.com/images/rq/6/6c/Pain7.png",
             9: "https://rq.bitplan.com/images/rq/2/29/Pain10.png",
            10: "https://rq.bitplan.com/images/rq/2/29/Pain10.png"
        }
        if rating in painImages:
            return f'<img alt="{rating}" src="{painImages[rating]}" width="32" height="32"/>'
        else:
            return ""

class ActionForm(FlaskForm):
    '''
    the action form
    '''
    queryTableSelection = HiddenField()
    actionTableSelection = HiddenField()
    submit = SubmitField("execute")


# TODO Removed functionality for current refactoring
# class RatingWidget(Widget):
#     '''
#     Displays a rating
#     '''
#
#     def __init__(self, rating:Rating):
#         super().__init__()
#         self.rating = rating
#
#     @staticmethod
#     def lookupPainImage(rating: int):
#         '''Returns html image tag to the corresponding pain rating'''
#         painImages = {
#              0: "http://rq.bitplan.com/images/rq/a/a3/Pain0.png",
#              1: "https://rq.bitplan.com/images/rq/0/01/Pain1.png",
#              2: "https://rq.bitplan.com/images/rq/0/01/Pain1.png",
#              3: "https://rq.bitplan.com/images/rq/0/0a/Pain4.png",
#              4: "https://rq.bitplan.com/images/rq/0/0a/Pain4.png",
#              5: "https://rq.bitplan.com/images/rq/b/b0/Pain6.png",
#              6: "https://rq.bitplan.com/images/rq/b/b0/Pain6.png",
#              7: "https://rq.bitplan.com/images/rq/6/6c/Pain7.png",
#              8: "https://rq.bitplan.com/images/rq/6/6c/Pain7.png",
#              9: "https://rq.bitplan.com/images/rq/2/29/Pain10.png",
#             10: "https://rq.bitplan.com/images/rq/2/29/Pain10.png"
#         }
#         if rating in painImages:
#             return f'<img alt="{rating}" src="{painImages[rating]}" width="32" height="32"/>'
#         else:
#             return ""
#
#     def render(self):
#         painImage = self.lookupPainImage(self.rating.pain)
#         return f'<span title="{self.rating.hint}">{self.rating.pain}{painImage}</span>'

if __name__ == '__main__':
    # construct the web application    
    web=WebServer()
    parser=web.getParser(description="dblp conference webservice")
    parser.add_argument('-s', '--source', default="orclone",help="wikiId of the source wiki [default: %(default)s]")   
    parser.add_argument('-t', '--target', default="myor",help="wikiId of the target wiki [default: %(default)s]") 
    parser.add_argument('--verbose',default=True,action="store_true",help="should relevant server actions be logged [default: %(default)s]")
    args=parser.parse_args()
    web.optionalDebug(args)
    web.verbose=args.verbose
    web.init(args.source,args.target)
    web.run(args)
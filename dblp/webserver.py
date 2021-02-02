'''
Created on 2020-12-30

@author: wf
'''
from fb4.app import AppWrap
from fb4.login_bp import LoginBluePrint
from fb4.sqldb import db
from fb4.widgets import Link, MenuItem
from flask import abort,flash,render_template, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from lodstorage.query import QueryManager
from lodstorage.sparql import SPARQL
from dblp.dblpxml import Dblp

import os
import json

from action.wikiaction import WikiAction
from wikibot.wikiuser import WikiUser
from wikibot.wikiclient import WikiClient
from wikibot.smw import SMW,SMWClient
from wtforms import HiddenField,SubmitField

class WebServer(AppWrap):
    ''' 
    dblp conf webserver
    '''
    
    def __init__(self, host='0.0.0.0', port=8252, debug=False,dblp=None):
        '''
        constructor
        
        Args:
            wikiId(str): id of the wiki to use as a CMS backend
            host(str): flask host
            port(int): the port to use for http connections
            debug(bool): True if debugging should be switched on
            dblp(Dblp): preconfigured dblp access (e.g. for mock testing)
        '''
        self.debug=debug
        self.dblp=dblp
        scriptdir = os.path.dirname(os.path.abspath(__file__))
        template_folder=scriptdir + '/../templates'
        super().__init__(host=host,port=port,debug=debug,template_folder=template_folder)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        db.init_app(self.app)
        self.db=db
        self.loginBluePrint=LoginBluePrint(self.app,'login')
        
        #
        # setup global handlers
        #
        @self.app.before_first_request
        def before_first_request_func():
            self.initDB()
            loginMenuList=self.adminMenuList("Login")
            self.loginBluePrint.setLoginArgs(menuList=loginMenuList)
            
        @self.app.route('/')
        def index():
            return self.index()
        
        @self.app.route('/sample/<entity>/<int:limit>')
        def showSample(entity,limit):
            return self.showSample(entity,limit)
        
        @self.app.route('/series/<series>')
        def showSeries(series):
            return self.showSeries(series)
        
        @self.app.route('/wikidata')
        def showWikiData():
            return self.showWikiData()
        
        @login_required
        @self.app.route('/lambdactions',methods=['GET', 'POST'])
        def showLambdaActions():
            return self.showLambdaActions()
        
    def initDB(self):
        '''
        initialize the database
        '''
        self.db.drop_all()
        self.db.create_all()
        self.initUsers()
        if self.dblp is None:
            self.dblp=Dblp()
        self.sqlDB=self.dblp.getXmlSqlDB()
        self.tableDict=self.sqlDB.getTableDict()
        
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
        for userid,wuser in enumerate(wusers.values()):
            username=self.getUserNameForWikiUser(wuser)
            self.loginBluePrint.addUser(self.db,username,wuser.getPassword(),userid=userid)
        
    def linkColumn(self,name,record,formatWith=None):
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
                record[name]=Link(lurl,value)
        
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
    
    def showWikiData(self):
        '''
        show the list of wikidata entries
        '''
        path="%s/../queries" % os.path.dirname(__file__)
        qm=QueryManager(lang='sparql',debug=False,path=path)
        endpoint="https://query.wikidata.org/sparql"
        sparql=SPARQL(endpoint)
        query=qm.queriesByName['Wikidata Conference Series']
        listOfDicts=sparql.queryAsListOfDicts(query.query,fixNone=True)
        for row in listOfDicts:
            row['confSeries']=Link(row['confSeries'],row['acronym'])
            if 'DBLP_pid':
                conf=row['DBLP_pid']
                if conf is None:
                    row['DBLP_pid']=""
                    row['conf']=''
                else:
                    conf=conf.replace("conf/","")
                    self.linkColumn('DBLP_pid',row, formatWith="https://dblp.org/db/%s")
                    row['conf']=Link(self.basedUrl(url_for("showSeries",series=conf)),conf)
            if 'WikiCFP_pid' in row:
                wikicfp_id=row['WikiCFP_pid']
                if wikicfp_id is None:
                    row['WikiCFP_pid']=""
                else:
                    title="wikicfp %s" % wikicfp_id
                    url="http://www.wikicfp.com/cfp/program?id=%s" % wikicfp_id
                    row['WikiCFP_pid']=Link(url,title)
            self.linkColumn('GND_pid', row, formatWith="https://lobid.org/gnd/%s")
            self.linkColumn("official_website", row)
                
        menuList=self.adminMenuList("wikidata")
        html=render_template("sample.html",title="wikidata",menuList=menuList,dictList=listOfDicts)
        return html
    
    def getSMWForLoggedInUser(self):
        wusers=WikiUser.getWikiUsers()
        luser=self.loginBluePrint.getLoggedInUser()
        smw=None
        wuser=None
        for wuser in wusers.values():
            username=self.getUserNameForWikiUser(wuser)
            if luser.username==username:
                wikiclient=WikiClient.ofWikiUser(wuser)
                smw=SMWClient(wikiclient.getSite())
                break
        return wuser,smw
        
    def showLambdaActions(self):
        '''
        show the available lambda Actions
        '''
        if not current_user.is_authenticated:
            abort(404)
        wuser,smw=self.getSMWForLoggedInUser()
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
    
        
    def showLambdaActionsForSMW(self,smw:SMW,wuser:WikiUser):
        '''
        show the lambad Actions for the given Semantic MediaWiki and wiki user
        
        Args:
            smw(SMW): the semantic mediawiki to use
        '''
        form = ActionForm()
        wikiurl=wuser.getWikiUrl()
        formatWith="%s/index.php/%%s" % wikiurl
        wikiAction=WikiAction(smw)
        sourceCodes=wikiAction.getSourceCodes()
        queryList=[]
        actionList=[]
        for orow in list(sourceCodes.values()):
            # get a copy of the row with the text column removed
            row=orow.copy()
            del row['text']
            self.linkColumn("Sourcecode", row, formatWith)
            lang=row['lang']
            if lang=='python':
                actionList.append(row)
            else:
                queryList.append(row)
        if form.validate_on_submit():
            actionName=self.getJsonColumn(form,"actionTableSelection",2)
            queryName=self.getJsonColumn(form,"queryTableSelection",2)
            lambdaAction=wikiAction.getLambdaAction("dblpconf-action",queryName,actionName)
            context={"sqlDB": self.sqlDB,"smw":smw}
            lambdaAction.execute(context)
            if 'result' in context:
                result=context['result']
                if 'message' in result:
                    message=result['message']
                    flash(message)
                   
        menuList=self.adminMenuList("actions")
        html=render_template("actions.html",form=form,title="actions",menuList=menuList,queryList=queryList,actionList=actionList)
        return html
             
    def showSample(self,entity:str,limit:int):
        '''
        Args:
            entity(str): the name of the entity to show the samples for
            limit(int): how many elements to show as a sample
        
        Returns:
            str: the html code or aborts with a 404 if the entity is invalid or 501 if the limit is above 5000
        '''
        
        if (not entity in self.tableDict):
            abort(404)
        elif limit>5000:
            abort(501)
        else:
            menuList=self.adminMenuList(entity)
            samples=self.sqlDB.query("select * from %s limit %d" % (entity,limit))
            for record in samples:
                self.linkRecord(record)
            html=render_template("sample.html",title=entity,menuList=menuList,dictList=samples)
            return html
        
    def basedUrl(self,url):
        '''
        add the base url if need be
        ''' 
        if url.startswith("/"):
            url="%s%s" % (self.baseUrl,url)
        return url
            
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
        for entity in self.tableDict.keys():
            url=url_for('showSample',entity=entity,limit=1000)
            title="%s" %entity
            menuList.append(MenuItem(url,title))
        menuList.append(MenuItem(url_for('showWikiData'),"wikidata"))
        if current_user.is_anonymous:
            menuList.append(MenuItem('/login','login'))
        else:
            menuList.append(MenuItem(url_for('showLambdaActions'),"actions"))
            menuList.append(MenuItem('/logout','logout'))
        
        if activeItem is not None:
            for menuItem in menuList:
                if menuItem.title==activeItem:
                    menuItem.active=True
                menuItem.url=self.basedUrl(menuItem.url)
        return menuList
    
    def index(self):
        '''
        show a conference overview
        '''
        menuList=self.adminMenuList("Home")
        query="""select conf,count(*) as count,min(year) as minYear,max(year) as maxYear
from proceedings 
where conf is not null
group by conf
order by 2 desc"""
        confs=self.sqlDB.query(query)
        for row in confs:
            conf=row['conf']
            row['series']=Link(self.basedUrl(url_for("showSeries",series=conf)),conf)
            row['conf']=Link("https://dblp.org/db/conf/%s/index.html" %conf,conf)
        html=render_template("sample.html",title="Event Series", dictList=confs,menuList=menuList)
        return html

class ActionForm(FlaskForm):
    '''
    the action form
    '''
    queryTableSelection = HiddenField()
    actionTableSelection = HiddenField()
    submit = SubmitField("execute")
    
if __name__ == '__main__':
    # construct the web application    
    web=WebServer()
    parser=web.getParser(description="dblp conference webservice")
    args=parser.parse_args()
    web.optionalDebug(args)
    web.run(args)
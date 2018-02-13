#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
from pyzabbix import ZabbixAPI, ZabbixAPIException
import os, sys, time, requests, pymysql.cursors
##############################################################################
# Settings
# URL domains file
UrlDomains = 'http://example.com/domains.txt'
# UserAgent
ZabbixUserAgent = 'Zabbix'
# 0 - not classified, 1 - information, 2 - warning, 3 - average, 4 - high, 5 - disaster
ZabbixTriggerPriority = 1
# Default HTTP code (if empty in file)
ZabbixDefaultHttpCode = 200
# Default checking domain timeout
ZabbixDefaultWebCheckTimeout = 180

# Zabbix database settings
ZabbixDbHost = 'localhost'
ZabbixDbName = 'zabbix'
ZabbixDbUser = 'zabbix'
ZabbixDbPass = 'zabbix'

# Zabbix API settings
ZabbixApiUrl = 'http://localhost'
ZabbixApiUser = 'zabbix'
ZabbixApiPass = 'zabbix'

# List monitoring hosts in Zabbix
MonitHosts= ['server1.example.com',
             'server2.example.com'
            ]
###########################################################################
# Functions
def Logger(msg):
    CurDate = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
    Write = str(CurDate +' - '+str(msg))
    print Write

def IsDownloadable(Url):
    Req = requests.head(Url, allow_redirects=True)
    Headers = Req.headers
    ContentType = Headers.get('content-type')
    if 'html' in ContentType.lower():
        return False
    return True

def CheckExistHost(HostName):
    SqlQuery = "SELECT hostid FROM hosts WHERE host = %s AND status=0"
    DbCursor.execute(SqlQuery, (HostName))
    HostId = DbCursor.fetchall()
    if HostId:
        return HostId[0][0]
    else:
        return False

def CheckExistDomainInHost(HostId, DomainName):
    SqlQuery = "SELECT httptestid FROM httptest WHERE hostid = %s AND name = %s"
    DbCursor.execute(SqlQuery, (HostId,DomainName,))
    DomainId = DbCursor.fetchall()
    if DomainId:
        return DomainId[0][0]
    else:
        return False

def AddDomainInHost(HostId, DomainName, Params):
    SplitArgs = Params.split(',')
    SetArgs = {}
    for ParseArgs in SplitArgs:
        Values = ParseArgs.split('=')
        Key = Values[0]
        Value = Values[1]
        SetArgs[Key] = Value
    HttpCode = SetArgs['HttpCode']
    Timeout = SetArgs['Timeout']
    Keywords = SetArgs['Keywords']
    try:
        RunApi = ApiConnect.httptest.create({"name": DomainName, "hostid": HostId, "agent": ZabbixUserAgent, "delay": int(Timeout),
                                    "steps": [{"no": 1, "name": "index", "url": "http://"+DomainName, "status_codes": HttpCode,"required": Keywords}]})
        return RunApi['httptestids'][0]
    except ZabbixAPIException as e:
        return e[0]
        sys.exit()

def CheckParamsDomain(DomainId, Params, ParamsValue):
    if Params == 'HttpCode':
        Value = 'status_codes'
    elif Params == 'Keywords':
        Value = 'required'
    elif Params == 'Timeout':
        Value = 'delay'
    SqlQuery = "SELECT {} FROM httptest ht,httpstep hp  WHERE hp.httptestid = {} AND ht.httptestid = hp.httptestid".format(Value,DomainId)
    DbCursor.execute(SqlQuery)
    ArgsValue = ParamsValue.strip()
    CursorValueInDb = DbCursor.fetchall()
    ValueInDb = str(CursorValueInDb[0][0]).strip()
    if ArgsValue == ValueInDb:
        return True
    else:
        return False

def UpdateParamsDomain(DomainId, DomainName, Args):
    SplitArgs = Args.split(',')
    SetArgs = {}
    for ParseArgs in SplitArgs:
        Values = ParseArgs.split('=')
        Key = Values[0]
        Value = Values[1]
        SetArgs[Key] = Value
    HttpCode = SetArgs['HttpCode']
    Timeout = SetArgs['Timeout']
    Keywords = SetArgs['Keywords']
    try:
        RunApi = ApiConnect.httptest.update({"httptestid": DomainId, "agent": ZabbixUserAgent, "delay": int(Timeout),
                                            "steps": [{"no": 1, "name": "index", "url": "http://" + DomainName, "status_codes": HttpCode,"required": Keywords}]})
    except ZabbixAPIException as e:
        return e[0]
        sys.exit()

def CheckExistTrigger(HostId, TriggerName):
    SqlQuery = "SELECT tr.triggerid FROM items it, functions fn, triggers tr WHERE it.hostid = %s AND it.itemid = fn.itemid AND fn.triggerid = tr.triggerid AND tr.description  = %s LIMIT 1"
    DbCursor.execute(SqlQuery, (HostId, TriggerName,))
    TriggerId = DbCursor.fetchall()
    if TriggerId:
        return TriggerId[0][0]
    else:
        return False

def AddTrigger(Host, DomainName):
    try:
        RunApi = ApiConnect.trigger.create({"description" : "WEB "+str(DomainName)+" failed", "hostid": CheckExistHost(Host),
                                            "expression": "{"+Host+":web.test.fail["+str(DomainName)+"].last(0)}<>0 and {"+Host+":web.test.fail["+str(DomainName)+"].last(#2)}<>0",
                                            "priority": ZabbixTriggerPriority})
        return RunApi['triggerids'][0]
    except ZabbixAPIException as e:
        return e[0]
        sys.exit()

def AddTriggerDependence(HostId, TriggerName, DependenceHostTriggerId):
    HostTriggerId = ApiConnect.trigger.get(output=['triggerid'], filter={"hostid": HostId, "description": TriggerName})[0]['triggerid']
    if HostTriggerId:
        try:
            RunApi = ApiConnect.trigger.adddependencies({"triggerid": HostTriggerId, "dependsOnTriggerid": DependenceHostTriggerId})
        except ZabbixAPIException as e:
            return e[0]
            sys.exit()

def CheckTriggerPriority(HostId, TriggerName, TriggerPriority):
    HostTriggerParams = ApiConnect.trigger.get(output=['triggerid','priority'], filter={"hostid": HostId, "description": TriggerName})[0]
    HostTriggerPriority = int(HostTriggerParams['priority'])
    if HostTriggerPriority == TriggerPriority:
        return True
    else:
        return HostTriggerParams['triggerid']


def UpdateTriggerPriority(TriggerId, TriggerPriority):
    try:
        RunApi = ApiConnect.trigger.update(
            {"triggerid": TriggerId, "priority": TriggerPriority})
    except ZabbixAPIException as e:
        return e[0]
        sys.exit()

# End Functions
############################################################################

Logger("Starting script ...")
StartTime = time.time()
if IsDownloadable(UrlDomains):
    Logger("Download domains from \""+str(UrlDomains)+"\".")
    Req = requests.get(UrlDomains, allow_redirects=True)
    with open('domains.txt', 'wb') as handle:
        for line in Req.iter_content(1024):
            handle.write(line)
    handle.close()

FileDomains = 'domains.txt'

if os.stat(FileDomains).st_size > 0:
    with open(FileDomains) as f:
        DomainCounts = str(sum(1 for _ in f))
    f.close()
    Logger("Found "+DomainCounts+" domains.")

    # Zabbix database connect
    try:
        DbConnect = pymysql.connect(host=ZabbixDbHost,user=ZabbixDbUser,password=ZabbixDbPass,db=ZabbixDbName,charset='utf8')
        DbCursor = DbConnect.cursor()
    except pymysql.err.OperationalError:
        Logger('ERROR: failed connect to database \"' + str(ZabbixDbName) + '\".')
        sys.exit()

    # Zabbix API connect
    try:
        ApiConnect = ZabbixAPI(ZabbixApiUrl)
        ApiConnect.login(ZabbixApiUser, ZabbixApiPass)
    except ZabbixAPIException as e:
        Logger(e[0])
        sys.exit()

else:
    Logger("File with domains is empty. Exit.")
    sys.exit()

for MonitHost in MonitHosts:
    if CheckExistHost(MonitHost):
        HostId = CheckExistHost(MonitHost)
        Logger('-' * 75)
        Logger("Starting process for host \"" + MonitHost + "\"...")
        n = 1
        DomainList = []
        FileOpen = open(FileDomains)
        for Line in FileOpen:
            Data = Line.split('\t')
            Id = str(Data[0].rstrip())
            DomainName = str(Data[1].rstrip())
            HttpCode = str(Data[2].rstrip())
            Keywords = Data[3].rstrip()
            Timeout = str(Data[4].rstrip())
            DependenceDomain = str(Data[5].rstrip())
            TriggerName = "WEB " + str(DomainName) + " failed"
            DomainList.append(DomainName)
            if len(HttpCode) == 0 or HttpCode == " " or HttpCode == False:
                HttpCode = ZabbixDefaultHttpCode
            if len(Timeout) == 0 or Timeout == " " or Timeout == False:
                Timeout = ZabbixDefaultWebCheckTimeout
            if len(Keywords) == 0 or Keywords == " " or Keywords == False:
                Keywords = ' '

            # Generate parameters for domain
            DomainParams = "HttpCode={},Timeout={},Keywords={}".format(HttpCode, Timeout, Keywords)

            # Check exist domain in host
            if CheckExistDomainInHost(HostId, DomainName):
                DomainId = CheckExistDomainInHost(HostId, DomainName)

                # Check domain parameters (httpcode, timeout and keywords)
                if CheckParamsDomain(DomainId, 'HttpCode', HttpCode) == False:
                    Logger(str(DomainName) + " -> update http code -> \""+str(HttpCode)+"\"")
                    UpdateParamsDomain(DomainId, DomainName, DomainParams)
                elif CheckParamsDomain(DomainId, 'Timeout', Timeout) == False:
                    Logger(str(DomainName) + " -> update timeout -> \"" + str(Timeout)+"\"")
                    UpdateParamsDomain(DomainId, DomainName, DomainParams)
                elif CheckParamsDomain(DomainId, 'Keywords', Keywords) == False:
                    Logger(str(DomainName) + " -> update keywords -> \"" + str(Keywords)+"\"")
                    UpdateParamsDomain(DomainId, DomainName, DomainParams)

                # Check exists trigger
                if CheckExistTrigger(HostId, TriggerName) == False:
                    Logger(str(DomainName) + " -> trigger not exist. Creating ...")
                    AddTrigger(MonitHost, DomainName)

            else:
                Logger(str(DomainName)+" -> not exist. Creating with params -> \""+str(DomainParams)+"\"")
                AddDomainInHost(HostId, DomainName, DomainParams)
                AddTrigger(MonitHost, DomainName)

            # Check priority trigger
            if CheckTriggerPriority(HostId, TriggerName, ZabbixTriggerPriority) != True:
                Logger(str(DomainName) + " -> update priority trigger -> \"" + str(ZabbixTriggerPriority)+"\"")
                TriggerId = CheckTriggerPriority(HostId, TriggerName, ZabbixTriggerPriority)
                UpdateTriggerPriority(TriggerId,ZabbixTriggerPriority)

            # Check and add trigger dependence
            for DependenceHost in MonitHosts:
                if DependenceHost != MonitHost:
                    DependenceHostId = CheckExistHost(DependenceHost)
                    GetDependenceHostTriggerId = ApiConnect.trigger.get(output=['triggerid'],filter={"hostid": DependenceHostId, "description": TriggerName})
                    if GetDependenceHostTriggerId:
                        DependenceHostTriggerId = GetDependenceHostTriggerId[0]['triggerid']
                        AddTriggerDependence(HostId, TriggerName, DependenceHostTriggerId)

            # Check and add trigger for domain dependence
            if DependenceDomain:
                DependenceDomainTriggerName = "WEB " + str(DependenceDomain) + " failed"
                GetDependenceDomainTriggerId = ApiConnect.trigger.get(output=['triggerid'],filter={"hostid": HostId, "description": DependenceDomainTriggerName})
                if GetDependenceDomainTriggerId:
                    DependenceDomainTriggerId = GetDependenceDomainTriggerId[0]['triggerid']
                    AddTriggerDependence(HostId, TriggerName, DependenceDomainTriggerId)



#            if n ==3 :
#                FileOpen.close()
#                break
            n += 1
        FileOpen.close()
        Logger("Finishing process for host \"" + MonitHost + "\".")
    else:
        Logger("ERROR: unknown host \""+str(MonitHost)+"\". Continue ...")
Logger('-' * 75)

# Remove non-exists domain in domains file
Logger("Searching non-existen domain in domains file ...")
for MonitHost in MonitHosts:
    if CheckExistHost(MonitHost):
        HostId = CheckExistHost(MonitHost)
        SqlQuery = " SELECT ht.name, ht.httptestid FROM hosts hs, httptest ht WHERE hs.hostid = %s AND hs.hostid = ht.hostid AND ht.status = 0"
        DbCursor.execute(SqlQuery, (HostId))
        DataFromZabbix = DbCursor.fetchall()
        for Data in DataFromZabbix:
            DomainInZabbix = str(Data[0]).rstrip()
            DomainIdInZabbix = Data[1]
            if DomainInZabbix not in DomainList:
                Logger(DomainInZabbix+" -> not exist in domais file. Remove this domain...")
                try:
                    RunApi = ApiConnect.httptest.delete(DomainIdInZabbix)
                except ZabbixAPIException as e:
                    print e[0]
                    sys.exit()


DbConnect.close()
Logger("Finishing script, elapsed: %s seconds." % round((time.time() - StartTime), 1))

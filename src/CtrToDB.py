import datetime
import glob
import csv
import re
import mysql.connector
import os
import dateutil.tz
import getopt
import sys
import logging


def cleanUtfSeqences(strIn):
    strClean = ''
    i=0
    while i < len(strIn):
        ## detect sequence of '\x' and take next two characters as hex
        if strIn[i] == chr(92) and strIn[i+1] == chr(120):
            bb = strIn[i+2:i+4]
            c = chr(int(bb, 16))
            i = i+4
        else:
            c = strIn[i]
            i = i+1
        strClean =strClean + c 
    return strClean





class CtrToDB:
  @staticmethod
  def registerConfigEntries(config):
    config['CtrToDB'] = {
       # 'DataDir': '/my/data/tmp/dir', # need it for isolated tests, but remove it for integration to not have double entry in config file
        'DB-host':'myDatabaseHost',
        'DB-user':'myDatabaseUser',
        'DB-pwd':'mySecretPassword',
        'DB-db': 'myDbName',
        'date-not-before': '2020-11-01'
        }


  def __init__(self,config):
    self.dictCounterNames = {}
    self.bBatchMode = False
    
    self.strDataDir = config['CtrToDB']['DataDir']
    self.strDbHost =  config['CtrToDB']['DB-host']
    self.strDbUser =  config['CtrToDB']['DB-user']
    self.strDbPwd =  config['CtrToDB']['DB-pwd']
    self.strDbDb =   config['CtrToDB']['DB-db']
    self.dtNotBefore = datetime.date.fromisoformat(config['CtrToDB']['date-not-before'])

  def openDB(self):
    self.mydb = mysql.connector.connect(host=self.strDbHost, 
    user=self.strDbUser, password=self.strDbPwd, database=self.strDbDb)
    self.mycursor = self.mydb.cursor()

  def closeDB(self):
    self.mydb.commit()
    self.mydb.close()



  def readIdMappingFromDB(self):
    logging.debug("readIdMappingFromDB()")
    self.openDB()
    self.mycursor.execute("SELECT counterId,CounterName from CounterNames")
    myresult = self.mycursor.fetchall()
    self.closeDB()
    if len(myresult) == 0:
      self.readIdMapping()
      self.updateIdMapping()
    for i in myresult:
            id = i[0]
            self.dictCounterNames[id] = i[1]



  '''
  Read all defined mappings from IDs to names and check for which of them 
  we have data files. 
  '''
  def readIdMapping(self):
    logging.debug("TransferCounter.readIdMapping()")
    strFName=self.strDataDir+'/Name-mapping.txt'
    f = open(strFName)
    for strLine in f:
        strFixedUtf = cleanUtfSeqences(strLine)
        ms=re.match('.*_(\d*)_Name=(.*)',strFixedUtf)
        if ms:
            id = int(ms[1])
            allFilesForCounter = glob.glob(self.strDataDir+'/FileDB/*/Linear/*'+str(id)+'_global_*_*_*.txt')
            if len(allFilesForCounter) > 0:
              self.dictCounterNames[id] = ms[2]


  '''
  Write name mapping to DB, drop table before
  '''
  def updateIdMapping(self):
    logging.debug("TransferCounter.updateIdMapping()")
    self.openDB()

    self.mycursor.execute("DROP TABLE IF EXISTS CounterNames")
    self.mycursor.execute("CREATE TABLE CounterNames (counterId INT PRIMARY KEY, counterName VARCHAR(255), counterGroup VARCHAR(255))")

    for id in self.dictCounterNames.keys():
        name = self.dictCounterNames[id]
        print('ID: {}  Name: {}'.format(id,name))
        cmd = "INSERT INTO CounterNames (counterId,counterName,counterGroup) VALUES (\'{}\',\'{}\',\'{}\')".format(id,name,'group')
        self.mycursor.execute(cmd)
    self.closeDB()
    


  def updateOneCounterAllFiles(self,CounterId,dtNotBefore):
    CounterName = self.dictCounterNames[CounterId]
    allFilesForCounter = glob.glob(self.strDataDir+'/FileDB/*/Linear/*'+str(CounterId)+'_global_*_*_*.txt')
    dateNotBefore = dtNotBefore.date()
    # for all date-files
    for strCFile in allFilesForCounter:
      ms = re.match('.*(\d*)_global_(\d*)_(\d*)_(\d*).txt',strCFile)
      year = int(ms[4])
      month = int(ms[2])
      day = int(ms[3])
      dtFileDate = datetime.date(year,month,day)
      if dtFileDate >=dateNotBefore:
        #logging.debug('updateing db for counter: {} Name: {}  date: {}'.format(CounterId,CounterName,dtFileDate))
        self.updateOneCounterOneFile(CounterId,strCFile,dtNotBefore)






  def updateOneCounterOneFile(self,CounterId,strCFile,dtNotBefore):
    # dtNotBefore = dtNotBefore-datetime.timedelta(hours=1) ## to debug time zone problem
    logging.debug("updateOneCounterOneFile({}, {}, {})".format(CounterId,strCFile,dtNotBefore.isoformat()))
    lstTupDay = []
    with open(strCFile) as csvfile:
        reader = csv.reader(csvfile,delimiter=';')
        for row in reader:
            strTS = row[0] # read timestamp
            intTS = int(strTS) #
            strValue = row[1]            
            DT = datetime.datetime.utcfromtimestamp(intTS)  
            # works on my system, but not inside podman/docker 
            # dtUtc = DT.astimezone(dateutil.tz.gettz('UTC'))
            #works as expected even inside container
            dtUtc = DT.astimezone(dateutil.tz.tzutc())
            fVal = float(strValue)
            if dtUtc > dtNotBefore:
              lstTupDay.append((intTS,dtUtc,fVal)) # time-stamp, datetime, float-value
            # print('     strDT: {}  dt: {}   value: {}'.format(strTS,DT,fVal))
    lstTupDay.sort(key=lambda tup: tup[0])
    self.sendData(CounterId, lstTupDay)


  def createTableName(self,cid):
    strTableName = "Ctr_{}_{}".format(cid,self.dictCounterNames[cid])
    strTableName = strTableName.replace(' ','_').replace('+','_').replace('-','_')
    return strTableName



  def prepareTable(self,counterId):
    strTabN = self.createTableName(counterId)
    self.openDB()    
    strCmd = "select table_name from information_schema.tables where table_schema='EMSdata' and table_name='{}'".format(strTabN)
    self.mycursor.execute(strCmd)
    myresult = self.mycursor.fetchall()
    if len(myresult) == 0:
      strCmd = "CREATE TABLE {} (time datetime PRIMARY KEY, value double)".format(strTabN)
      self.mycursor.execute(strCmd)
    self.closeDB()


  def clearCounterTables(self):
    self.openDB()
    strCmd = "select table_name from information_schema.tables where table_schema='EMSdata' and table_name like 'Ctr\_%'"
    self.mycursor.execute(strCmd)
    myresult = self.mycursor.fetchall()
    for line in myresult:
      strCmd = "DROP TABLE {}".format(line[0])
      self.mycursor.execute(strCmd)
    self.closeDB()



  def sendData(self,cId, lstTup):
    strTabN = self.createTableName(cId) 
    self.openDB()
    strVals =""
    if self.bBatchMode: # fast, but not robust against double inserts
      for (intTS,dtUtc,fVal) in lstTup:
        strUtc = dtUtc.strftime('%Y-%m-%d %H:%M:%S')
        if len(strVals)>0:
          strVals = strVals+','
        strVals = strVals+"('{}',{})".format(strUtc,fVal )
      strCmd = "INSERT INTO {} (time, value) VALUES ".format(strTabN) + strVals
      self.mycursor.execute(strCmd)
    else: 
      # update each row with a single call, very slow
      for (intTS,dtUtc,fVal) in lstTup:
        strUtc = dtUtc.strftime('%Y-%m-%d %H:%M:%S')
        strCmd = "INSERT INTO {} (time, value) VALUES ('{}',{})".format(strTabN,strUtc,fVal )
        try:
          self.mycursor.execute(strCmd)
        except Exception as e:
          logging.error("SQL failed: {}, {}".format(e,strCmd))

    self.closeDB()




  def getLatestEntry(self,cId):
    strTabN = self.createTableName(cId) 
    self.openDB()
    strCmd = "select time from {} order by time desc limit 1".format(strTabN);
    self.mycursor.execute(strCmd)
    myresult = self.mycursor.fetchall()
    if len(myresult) == 0:
      result = datetime.datetime(2020,11,13).astimezone(dateutil.tz.tzutc()) # take earliest reasaonable date
    else:
      result = myresult[0][0].replace(tzinfo=dateutil.tz.tzutc())
    self.closeDB()
      
    return result


  def updateAllCounter(self):
    logging.debug("TransferCounter.updateAllCounter()")

    for CounterId in self.dictCounterNames.keys():
      self.prepareTable(CounterId)
      dtNotBefore = self.getLatestEntry(CounterId)
      self.updateOneCounterAllFiles(CounterId, dtNotBefore)






 
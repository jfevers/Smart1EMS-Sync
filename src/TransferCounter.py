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





class TransferCounter:
  @staticmethod
  def registerConfigEntries(config):
    config['TransferCounter'] = {
        'DataDir': '/my/data/tmp/dir',
        'DB-host':'myDatabaseHost',
        'DB-user':'myDatabaseUser',
        'DB-pwd':'mySecretPassword',
        'DB-db': 'myDbName',
        'Ems-address':'name_or_ip_of_EMS',
        'SSH-ID': 'id_or_file_with_priv_key',
        'date-not-before': '2020-11-01'
        }


  def __init__(self,config):
    self.dictCounterNames = {}
    self.bBatchMode = False

    self.strDataDir = config['TransferCounter']['DataDir']
    self.strDbHost =  config['TransferCounter']['DB-host']
    self.strDbUser =  config['TransferCounter']['DB-user']
    self.strDbPwd =  config['TransferCounter']['DB-pwd']
    self.strDbDb =   config['TransferCounter']['DB-db']
    self.strSshId = config['TransferCounter']['SSH-ID']
    self.strEmsAddr=config['TransferCounter']['ems-address']
    self.strScpBase = "scp -r -o \"KexAlgorithms +diffie-hellman-group1-sha1\" -o StrictHostKeyChecking=no -i {} root@{}:/Smart1".format(self.strSshId,self.strEmsAddr)
    self.dtNotBefore = datetime.date.fromisoformat(config['TransferCounter']['date-not-before'])

  def openDB(self):
    self.mydb = mysql.connector.connect(host=self.strDbHost, 
    user=self.strDbUser, password=self.strDbPwd, database=self.strDbDb)
    self.mycursor = self.mydb.cursor()

  def closeDB(self):
    self.mydb.commit()
    self.mydb.close()


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


  def updateFiles(self, bAll=False, numDaysBack=0): 
    logging.debug("TransferCounter.updateFiles()")
    strRedirectStdout = " >>{}/FileCopy.log".format(self.strDataDir)
    strTargetDir = self.strDataDir+"/FileDB"

    with open("{}/FileCopy.log".format(self.strDataDir),'a+') as f:
      f.write("{} updateFiles(bAll={}, numDaysBack={})\n".format(datetime.datetime.now().isoformat(),bAll, numDaysBack))

    if bAll:
    # complete history
      strCmd = self.strScpBase + "/FileDB/* {}/".format(strTargetDir)
      res = os.system(strCmd + strRedirectStdout)
      if res != 0:
        raise Exception("Command failed: "+strCmd)
    else:
      useDate = datetime.date.today()
      useDate = useDate- datetime.timedelta(days=numDaysBack)
      # only one day
      strPattern = "*global_{}_{}_{}.txt".format(useDate.month,useDate.day,useDate.year)
         # copy buscounter, calculationcounter, ... from Linear/
      strCmd = self.strScpBase + "/FileDB/{}/Linear/{} {}/{}/Linear/".format(useDate.year,strPattern,strTargetDir,useDate.year)
      res = os.system(strCmd + strRedirectStdout)
      if res != 0:
        raise Exception("Command failed: "+strCmd)
   
      lstSubDirs =["B1_A5_S1","B2_A1_S1","B2_A1_S2"] 
      for strSd in lstSubDirs:
        # copy raw bus counter data
        strCmd = self.strScpBase + "/FileDB/{}/{}/{}  {}/{}/{}".format(useDate.year,strSd,strPattern,strTargetDir,useDate.year,strSd)
        res = os.system(strCmd + strRedirectStdout)
        if res != 0:
          logging.error("Command failed, but ignoring: "+strCmd)
          #raise Exception("Command failed: "+strCmd)






  def checkAndPrepareDirectories(self):
    strTarget1 = self.strDataDir+"/FileDB"
    if not os.path.isdir(strTarget1):
      os.mkdir(strTarget1)

    strInitalSyncDone = self.strDataDir+"/InitialSyncDone.txt"
    self.strNameFile = self.strDataDir+"/Name-mapping.txt"
    bRunFirstFlush = False

    if not os.path.isfile(strInitalSyncDone):
      logging.info("Did not found {}, resetting DB and init from EMS completely".format(strInitalSyncDone))
      with open(strInitalSyncDone,"w") as f:
        f.write(datetime.datetime.now().isoformat())
      self.updateFiles(bAll=True)
      self.clearCounterTables()
      bRunFirstFlush = True

    # prepare name-mapping file and read it  
    if not os.path.isfile(self.strNameFile):
      strCmd = self.strScpBase + "/smart1.conf {}/".format(self.strDataDir)
      logging.debug("cmd: "+strCmd)
      res = os.system(strCmd)
      if res != 0:
        raise Exception("Command failed: "+strCmd)
      strCmd = "grep Name {}/smart1.conf > {}".format(self.strDataDir,self.strNameFile)
      res = os.system(strCmd)
      if res != 0:
        raise Exception("Command failed: "+strCmd)
      self.readIdMapping()
      self.updateIdMapping() # do not update every time
    else:
      self.readIdMapping()

    if bRunFirstFlush:
      logging.info("running first big update for all counters")
      self.bBatchMode = True
      self.updateAllCounter()
      self.bBatchMode = False

import datetime
import glob
import csv
import re
import numpy as np
import mysql.connector
import os
import dateutil.tz
import getopt
import sys





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
        'SSH-ID': 'id_or_file_with_priv_key'
        }


  def __init__(self,config):
    self.dictCounterNames = {}
    self.dictCounterData ={} 
    self.strMyDir = os.path.dirname(os.path.realpath(__file__))

    self.strDataDir = config['TransferCounter']['DataDir']
    self.strDbHost =  config['TransferCounter']['DB-host']
    self.strDbUser =  config['TransferCounter']['DB-user']
    self.strDbPwd =  config['TransferCounter']['DB-pwd']
    self.strDbDb =   config['TransferCounter']['DB-db']
    self.strSshId = config['TransferCounter']['SSH-ID']
    self.strEmsAddr=config['TransferCounter']['ems-address']


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
    strFName=self.strMyDir+'/Name-mapping.txt'
    f = open(strFName)
    for line in f:
        ms=re.match('.*_(\d*)_Name=(.*)',line)
        if ms:
            id = int(ms[1])
            allFilesForCounter = glob.glob(self.strDataDir+'*/Linear/*'+str(id)+'_global_*_*_*.txt')
            if len(allFilesForCounter) > 0:
              self.dictCounterNames[id] = ms[2]


  '''
  Write name mapping to DB, drop table before
  '''
  def updateIdMapping(self):
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
    allFilesForCounter = glob.glob(self.strBasedir+'*/Linear/*'+str(CounterId)+'_global_*_*_*.txt')
    dateNotBefore = dtNotBefore.date()
    # for all date-files
    for strCFile in allFilesForCounter:
      ms = re.match('.*(\d*)_global_(\d*)_(\d*)_(\d*).txt',strCFile)
      year = int(ms[4])
      month = int(ms[2])
      day = int(ms[3])
      dtFileDate = datetime.date(year,month,day)
      if dtFileDate >=dateNotBefore:
        print('BC: {} Name: {}  date: {}'.format(CounterId,CounterName,dtFileDate))
        self.updateOneCounterOneFile(CounterId,strCFile,dtNotBefore)






  def updateOneCounterOneFile(self,CounterId,strCFile,dtNotBefore):
    lstTupDay = []
    with open(strCFile) as csvfile:
        reader = csv.reader(csvfile,delimiter=';')
        for row in reader:
            strTS = row[0] # read timestamp
            intTS = int(strTS) # correct by -1 hour
            strValue = row[1]
            
            DT = datetime.datetime.utcfromtimestamp(intTS)  
            dtUtc = DT.astimezone(dateutil.tz.gettz('UTC'))
            fVal = float(strValue)
            if dtUtc > dtNotBefore:
              lstTupDay.append((intTS,dtUtc,fVal)) # time-stamp, datetime, float-value
            # print('     strDT: {}  dt: {}   value: {}'.format(strTS,DT,fVal))
    lstTupDay.sort(key=lambda tup: tup[0])
    self.dictCounterData[CounterId].extend(lstTupDay)
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
    for (intTS,dtUtc,fVal) in lstTup:
#      if len(strVals)>0:
#        strVals = strVals+','
#      strVals = strVals+"({},{})".format(DT.isoformat(),fVal )
      strUtc = dtUtc.strftime('%Y-%m-%d %H:%M:%S')

      strCmd = "INSERT INTO {} (time, value) VALUES ('{}',{})".format(strTabN,strUtc,fVal )

    #strCmd = "INSERT INTO {} (time, value) VALUES ".format(strTabN) + strVals

      self.mycursor.execute(strCmd)
    self.closeDB()




  def getLatestEntry(self,cId):
    strTabN = self.createTableName(cId) 
    self.openDB()
    strCmd = "select time from {} order by time desc limit 1".format(strTabN);
    self.mycursor.execute(strCmd)
    myresult = self.mycursor.fetchall()
    if len(myresult) == 0:
      result = datetime.datetime(2020,11,13) # take earliest reasaonable date, TZ does not matter here
    else:
      result = myresult[0][0].replace(tzinfo=dateutil.tz.gettz('UTC'))
    self.closeDB()
      
    return result


  def updateAllCounter(self):
    for CounterId in self.dictCounterNames.keys():
      self.prepareTable(CounterId)
      dtNotBefore = self.getLatestEntry(CounterId)
      self.dictCounterData[CounterId] =[] 
      self.updateOneCounterAllFiles(CounterId, dtNotBefore)


  def updateFiles(self, bAll=False, numDaysBack=0): 
    strTargetDir = self.strDataDir+"/FileDB/2020"

    strScpBase = "scp -r -o \"KexAlgorithms +diffie-hellman-group1-sha1\" -i {} root@{}:/Smart1/FileDB".format(self.strSshId,self.strEmsAddr)
    useDate = datetime.date.today()
    useDate = useDate- datetime.timedelta(days=numDaysBack)
    if bAll:
    # complete history
      strPattern = "*global_*.txt" ## global
    else:
      # only one day
      strPattern = "*global_{}_{}_{}.txt".format(useDate.month,useDate.day,useDate.year)
   
    # copy buscounter, calculationcounter, ... from Linear/
    strCmd = strScpBase + "/{}/Linear/{} {}/Linear/".format(useDate.year,strPattern,strTargetDir)
    res = os.system(strCmd)
    if res != 0:
      raise("Command failed: "+strCmd)

   
    lstSubDirs =["B1_A5_S1","B2_A1_S1","B2_A1_S2"] 
    for strSd in lstSubDirs:
      # copy raw bus counter data
      strCmd = strScpBase + "/{}/{}/{}  {}/{}".format(useDate.year,strSd,strPattern,strTargetDir,strSd)
      res = os.system(strCmd)
      if res != 0:
        raise("Command failed: "+strCmd)


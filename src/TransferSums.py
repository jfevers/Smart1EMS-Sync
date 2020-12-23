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





class TransferSums:
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
    self.bBatchMode = False

    self.strDataDir = config['TransferCounter']['DataDir']
    self.strDbHost =  config['TransferCounter']['DB-host']
    self.strDbUser =  config['TransferCounter']['DB-user']
    self.strDbPwd =  config['TransferCounter']['DB-pwd']
    self.strDbDb =   config['TransferCounter']['DB-db']
    self.strSshId = config['TransferCounter']['SSH-ID']
    self.strEmsAddr=config['TransferCounter']['ems-address']
    self.strScpBase = "scp -r -o \"KexAlgorithms +diffie-hellman-group1-sha1\" -o StrictHostKeyChecking=no -i {} root@{}:/Smart1".format(self.strSshId,self.strEmsAddr)
    self.dtNotBefore = datetime.date.fromisoformat('2020-11-01')

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
  def readIdMappingFromDB(self):
    logging.debug("readIdMappingFromDB()")
    self.openDB()
    self.mycursor.execute("SELECT counterId,CounterName from CounterNames")
    myresult = self.mycursor.fetchall()
    self.closeDB()
    for i in myresult:
            id = i[0]
            self.dictCounterNames[id] = i[1]


  

  def updateOneCounterAllFiles(self,CounterId):
    CounterName = self.dictCounterNames[CounterId]
    # for all sum-per-day files
    allFilesForSumDays = glob.glob(self.strDataDir+'/FileDB/*/Linear/*'+str(CounterId)+'_avg_day_*_*.txt')
    lstTupAll = []
    for strCFile in allFilesForSumDays:
        ms = re.match('.*(\d*)_avg_day_(\d*)_(\d*).txt',strCFile)
        year = int(ms[3])
        month = int(ms[2])
        lstTupOne = self.updateOneCounterOneFileDays(CounterId,strCFile,year,month)
        lstTupAll.extend(lstTupOne)
    lstTupAll.sort(key=lambda tup: tup[0])
    self.sendData(CounterId, lstTupAll)

    # for all sum-per-month files
    lstTupAll = []
    allFilesForSumMonth = glob.glob(self.strDataDir+'/FileDB/*/Linear/*'+str(CounterId)+'_avg_month_*.txt')
    # for all date-files
    for strCFile in allFilesForSumMonth:
        ms = re.match('.*(\d*)_avg_month_(\d*).txt',strCFile)
        year = int(ms[2])
        lstTupOne = self.updateOneCounterOneFileMonths(CounterId,strCFile,year)
        lstTupAll.extend(lstTupOne)
    lstTupAll.sort(key=lambda tup: tup[0])
    self.sendData(CounterId, lstTupAll)





  def updateOneCounterOneFileDays(self,CounterId,strCFile,year,month):
    # dtNotBefore = dtNotBefore-datetime.timedelta(hours=1) ## to debug time zone problem
    logging.debug("updateOneCounterOneFileDays({}, {})".format(CounterId,strCFile))
    lstTupDay = []
    with open(strCFile) as csvfile:
        reader = csv.reader(csvfile,delimiter=';')
        for row in reader:
            try:
                day = int(row[0]) # read timestamp
                dt = datetime.date(year,month,day)
                if dt >= self.dtNotBefore:
                    strValue = row[1]            
                    fVal = float(strValue)
                    strId = '{}-{:02d}-{:02d}'.format(year,month,day)
                    lstTupDay.append((strId, year,month,day,fVal))
            except Exception as e:
                logging.error("Failed to parse file {}, line {} with exception: {}".format(strCFile,row,e))
    return lstTupDay
   

  def updateOneCounterOneFileMonths(self,CounterId,strCFile,year):
    logging.debug("updateOneCounterOneFileMonths({}, {})".format(CounterId,strCFile))
    lstTupMonth = []
    with open(strCFile) as csvfile:
        reader = csv.reader(csvfile,delimiter=';')
        for row in reader:
            if len(row) > 0:
                month = int(row[0]) # read timestamp
                dt = datetime.date(year,month,1)
                if dt >= self.dtNotBefore:
                    strValue = row[1]            
                    fVal = float(strValue)
                    strId = '{}-{:02d}-{:02d}'.format(year,month,0)
                    lstTupMonth.append((strId, year,month,0,fVal))
    return lstTupMonth



  def createTableName(self,cid):
    strTableName = "Sum_{}_{}".format(cid,self.dictCounterNames[cid])
    strTableName = strTableName.replace(' ','_').replace('+','_').replace('-','_')
    return strTableName



  def prepareTable(self,counterId):
    strTabN = self.createTableName(counterId)
    self.openDB()    
    strCmd = "select table_name from information_schema.tables where table_schema='EMSdata' and table_name='{}'".format(strTabN)
    self.mycursor.execute(strCmd)
    myresult = self.mycursor.fetchall()
    if len(myresult) == 0:
      strCmd = "CREATE TABLE {} (id varchar(50), year int, month int, day int, value double,PRIMARY KEY(id))".format(strTabN)
      self.mycursor.execute(strCmd)
    self.closeDB()


  def clearSumTables(self):
    self.openDB()
    strCmd = "select table_name from information_schema.tables where table_schema='EMSdata' and table_name like 'Sum\_%'"
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
    for (strId, year,month,day,fVal) in lstTup:
        if len(strVals)>0:
            strVals = strVals+','
        strVals = strVals+"('{}',{},{},{},{})".format(strId,year,month,day,fVal )
    strCmd = "INSERT INTO {} (id, year, month, day, value) VALUES ".format(strTabN) + strVals
    self.mycursor.execute(strCmd)
    self.closeDB()




  def updateAllSums(self):
      logging.debug("updateAllSums()")
      self.clearSumTables()
      for CounterId in self.dictCounterNames.keys():
          self.prepareTable(CounterId)
          self.updateOneCounterAllFiles(CounterId, )









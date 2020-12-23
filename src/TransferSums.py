import datetime
import glob
import csv
import re
import mysql.connector
import os
import logging
import TransferCounter





class TransferSums(TransferCounter.TransferCounter):
 

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
  

  def updateOneCounterAllSumFiles(self,CounterId):
    CounterName = self.dictCounterNames[CounterId]
    # for all sum-per-day files
    allFilesForSumDays = glob.glob(self.strDataDir+'/FileDB/*/Linear/*'+str(CounterId)+'_avg_day_*_*.txt')
    lstTupAll = []
    for strCFile in allFilesForSumDays:
        ms = re.match('.*(\d*)_avg_day_(\d*)_(\d*).txt',strCFile)
        year = int(ms[3])
        month = int(ms[2])
        lstTupOne = self.updateOneCounterOneSumFileDays(CounterId,strCFile,year,month)
        lstTupAll.extend(lstTupOne)
    lstTupAll.sort(key=lambda tup: tup[0])
    self.sendSumData(CounterId, lstTupAll)

    # for all sum-per-month files
    lstTupAll = []
    allFilesForSumMonth = glob.glob(self.strDataDir+'/FileDB/*/Linear/*'+str(CounterId)+'_avg_month_*.txt')
    # for all date-files
    for strCFile in allFilesForSumMonth:
        ms = re.match('.*(\d*)_avg_month_(\d*).txt',strCFile)
        year = int(ms[2])
        lstTupOne = self.updateOneCounterOneSumFileMonths(CounterId,strCFile,year)
        lstTupAll.extend(lstTupOne)
    lstTupAll.sort(key=lambda tup: tup[0])
    self.sendSumData(CounterId, lstTupAll)



  def updateOneCounterOneSumFileDays(self,CounterId,strCFile,year,month):
    # dtNotBefore = dtNotBefore-datetime.timedelta(hours=1) ## to debug time zone problem
    logging.debug("updateOneCounterOneSumFileDays({}, {})".format(CounterId,strCFile))
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
   

  def updateOneCounterOneSumFileMonths(self,CounterId,strCFile,year):
    logging.debug("updateOneCounterOneSumFileMonths({}, {})".format(CounterId,strCFile))
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



  def createSumTableName(self,cid):
    strTableName = "Sum_{}_{}".format(cid,self.dictCounterNames[cid])
    strTableName = strTableName.replace(' ','_').replace('+','_').replace('-','_')
    return strTableName



  def prepareSumTable(self,counterId):
    strTabN = self.createSumTableName(counterId)
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



  def sendSumData(self,cId, lstTup):
    strTabN = self.createSumTableName(cId) 
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
          self.prepareSumTable(CounterId)
          self.updateOneCounterAllSumFiles(CounterId, )









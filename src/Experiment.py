import datetime
import glob
import csv
import re
import numpy as np
import matplotlib.pyplot as plt
import mysql.connector




class EMSDataTransfer:
  def __init__(self):
    self.dictCounterNames = {}
    self.strBasedir = '/home/friso/Unsafed/EMS-Data/FileDB/'
    self.dictCounterData ={} 


  def readIdMapping(self):
    strFName='/home/friso/src/EMS-Readout/src/Name-mapping.txt'
    f = open(strFName)
    for line in f:
        ms=re.match('.*_(\d*)_Name=(.*)',line)
        if ms:
            id = int(ms[1])
            self.dictCounterNames[id] = ms[2]



  def updateIdMapping(self):
    mydb = mysql.connector.connect(host="lala", user="EMSrw", password="NMe47u27gzsa", database="EMSdata")
    mycursor = mydb.cursor()

    mycursor.execute("SHOW TABLES")
    for x in mycursor:
      print(x) 

    mycursor.execute("DROP TABLE IF EXISTS CounterNames")
    mycursor.execute("CREATE TABLE CounterNames (counterId INT PRIMARY KEY, counterName VARCHAR(255), counterGroup VARCHAR(255))")

    for id in self.dictCounterNames.keys():
        name = self.dictCounterNames[id]
        print('ID: {}  Name: {}'.format(id,name))
        cmd = "INSERT INTO CounterNames (counterId,counterName,counterGroup) VALUES (\'{}\',\'{}\',\'{}\')".format(id,name,'group')
        mycursor.execute(cmd)

    mydb.commit()
    mydb.close()


  def updateOneCounterAllFiles(self,CounterId,dtNotBefore):
    CounterName = self.dictCounterNames[CounterId]
    #for globbing
    strYear = '2020'
    strMonth = '11'
    strDay = '23'

    allFilesForCounter = glob.glob(self.strBasedir+strYear+'/Linear/*'+str(CounterId)+'_global_'+strMonth+'_'+strDay+'_'+strYear+'.txt')

    # for all date-files
    for strCFile in allFilesForCounter:
      ms = re.match('.*(\d*)_global_(\d*)_(\d*)_(\d*).txt',strCFile)
      strDate=ms[4]+'-'+ms[2]+'-'+ms[3]
      print('BC: {} Name: {}  date: {}'.format(CounterId,CounterName,strDate))
      self.updateOneCounterOneFile(CounterId,strCFile,dtNotBefore)






  def updateOneCounterOneFile(self,CounterId,strCFile,dtNotBefore):
    lstTupDay = []
    with open(strCFile) as csvfile:
        reader = csv.reader(csvfile,delimiter=';')
        for row in reader:
            strTS = row[0] # read timestamp
            intTS = int(strTS) - 3600 # correct by -1 hour
            strValue = row[1]
            DT = datetime.datetime.fromtimestamp(intTS)  
            fVal = float(strValue)
            lstTupDay.append((intTS,DT,fVal))
            # print('     strDT: {}  dt: {}   value: {}'.format(strTS,DT,fVal))
    lstTupDay.sort(key=lambda tup: tup[0])
    self.dictCounterData[CounterId].extend(lstTupDay)



  def updateAllCounter(self):
    ### for debugging only
    # self.dictCounterNames.clear()
    # self.dictCounterNames[1526466858] = 'Überschuss CGout[W]'

    dtNotBefore = datetime.datetime(2020,11,23)

    for CounterId in self.dictCounterNames.keys():
      self.dictCounterData[CounterId] =[] 
      self.updateOneCounterAllFiles(CounterId, dtNotBefore)





myUpdater = EMSDataTransfer()
myUpdater.readIdMapping()
#myUpdater.updateIdMapping()
myUpdater.updateAllCounter()


dictPlotIt  ={} 
  # buscounter
#dictPlotIt[1526658041] = 'Netzfrequzne [Hz]'
dictPlotIt[1526471785] = 'WP Bezug' # 0
dictPlotIt[1526466886] = 'Bezug' # 
dictPlotIt[1526466858] = 'Überschuss' # ? korreliert mit 1526467213 und 1526471371
#dictPlotIt[1526467140] = 'Heizstab Bezug' # 0
# calculation counter
#dictPlotIt[1526467264] = 'Bezug-HZ' # 0
#dictPlotIt[1526467826] = 'Bezug-HZ-ECAR' # 0 
#dictPlotIt[1526467678] = 'Überschuss+HZ+ECAR' # 0 
#dictPlotIt[1526477230] = 'Gesamtverbrauch' # 0
#dictPlotIt[1526467213] = 'Überschuss+HZ' # 500 - 2500
dictPlotIt[1526477645] = 'Hausstrom' # 0 
#dictPlotIt[1526471371] = 'Überschuss+HZ+ECAR+Laden-Entlade' 
#dictPlotIt[1526477597] = 'Wärmestrom' # 0 
#dictPlotIt[1526471474] = 'Bezug-HZ-ECAR-Discharge+Charge'
# regulation
#dictPlotIt[1526495469] = 'BATT Power'
dictPlotIt[1526495508] = 'Grid Power'
# remote counter
#dictPlotIt[1526469030] = 'BATT Laden'
dictPlotIt[1532951436] = 'PV DC Seitig'
# pv_global
dictPlotIt[1526476850] = 'PV Erzeugung'
# remotesensor
#dictPlotIt[1526468849] = 'BATT V'
#dictPlotIt[1526468909] = 'Max Laden' # const 3000
#dictPlotIt[1526471294] = 'BATT A'
#dictPlotIt[1526468812] = 'BATT Ladezustand'
#dictPlotIt[1526468926] = 'Max Entladen'



lstLegend = []
for cid in dictPlotIt.keys():
  lstLegend.append(str(cid)+'  '+myUpdater.dictCounterNames[cid])
  data = np.array(myUpdater.dictCounterData[cid])
  plt.plot(data[:,1],data[:,2],'.')
  plt.legend(lstLegend)
plt.show()

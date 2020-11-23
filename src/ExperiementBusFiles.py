import datetime
import glob
import csv
import re
import numpy as np
import matplotlib.pyplot as plt
import mysql.connector




class EMSDataTransfer:
  def __init__(self):
    self.dictBusNames = {}
    self.dictBusNames['B1_A5_S1'] = 'PV DC'
    self.dictBusNames['B2_A1_S1'] = 'WR1 S1'
    self.dictBusNames['B2_A1_S2'] = 'WR1 S2'

    self.strBasedir = '/home/friso/Unsafed/EMS-Data/FileDB/'
    self.dictBusData ={} 


  def updateOneBusAllFiles(self,BusId,dtNotBefore):
    BusName = self.dictBusNames[BusId]
    allFilesForCounter = glob.glob(self.strBasedir+'*/'+str(BusId)+'/global_*_*_*.txt')

    # for all date-files
    for strCFile in allFilesForCounter:
      ms = re.match('.*/global_(\d*)_(\d*)_(\d*).txt',strCFile)
      year = int(ms[3])
      month = int(ms[1])
      day = int(ms[2])
      dtFileDate = datetime.datetime(year,month,day)
      print('BC: {} Name: {}  date: {}'.format(BusId,BusName,dtFileDate))
      if dtFileDate >=dtNotBefore:
        self.updateOneBusOneFile(BusId,strCFile,dtNotBefore)






  def updateOneBusOneFile(self,BusId,strCFile,dtNotBefore):
    lstTupDay = []
    lastTS=0
    with open(strCFile) as csvfile:
        reader = csv.reader(csvfile,delimiter=';')
        for row in reader:
            strTS = row[0] # read timestamp
            intTS = int(strTS) - 3600 # correct by -1 hour
            #    0      ;1;2;3;4; 5 ; 6 ; 7 ;8
            # 1606142810;5;1;1;1;360;360;500;0    #B1_A5_S1
            # 1606141010;1;2;2;1;275;274;302;33   #B2_A1_S1
            # 1606144609;1;2;2;2;172;151;292;33   #B2_A1_S1

            strValue = row[8]
            DT = datetime.datetime.fromtimestamp(intTS)  
            fVal = float(strValue)
            lstTupDay.append((intTS,DT,fVal))
            # print('     strDT: {}  dt: {}   value: {}'.format(strTS,DT,fVal))
    lstTupDay.sort(key=lambda tup: tup[0])
    self.dictBusData[BusId].extend(lstTupDay)
 
  def updateAllBusses(self):
    ### for debugging only
    # self.dictCounterNames.clear()
    # self.dictCounterNames[1526466858] = 'Überschuss CGout[W]'
    dtNotBefore = datetime.datetime(2020,11,23)
    for BusId in self.dictBusNames.keys():
      self.dictBusData[BusId] =[] 
      self.updateOneBusAllFiles(BusId, dtNotBefore)





myUpdater = EMSDataTransfer()
myUpdater.updateAllBusses()




lstLegend = []
for cid in myUpdater.dictBusData.keys():
  lstLegend.append(str(cid)+'  '+myUpdater.dictBusNames[cid])
  data = np.array(myUpdater.dictBusData[cid])
  plt.plot(data[:,1],data[:,2],'.')
  plt.legend(lstLegend)
plt.show()

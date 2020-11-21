import datetime
import glob
import csv
import re
import numpy as np
import matplotlib.pyplot as plt


#dt = datetime.datetime.now()
#ts = dt.timestamp()
#t = dt.time()
#print(t)
#print(ts)

dictCounterNames = {}
# # buscounter
# dictCounterNames[1526658041] = 'Frequency [Hz]'
# dictCounterNames[1526471785] = '?' # 0
dictCounterNames[1526466886] = 'Bezug CGin [W]' # noch mal abends prüfen
dictCounterNames[1526466858] = 'Überschuss CGout[W]' # ? korreliert mit 1526467213 und 1526471371
# dictCounterNames[1526467140] = '?' # 0
# 
# # calculation counter
# dictCounterNames[1526467264] = '?' # 0
# dictCounterNames[1526467826] = '?' # 0 
# dictCounterNames[1526467678] = '?' # 0 
# dictCounterNames[1526477230] = '?' # 0
dictCounterNames[1526467213] = '?' # 500 - 2500
# dictCounterNames[1526477645] = '?' # 0 
dictCounterNames[1526471371] = '?' # etwas größer als 1526467213
# dictCounterNames[1526477597] = '?' # 0 
# dictCounterNames[1526471474] = 'Batt laden [W]'


# regulation
#dictCounterNames[1526495469] = 'regulation ?'  # 100 - 160 ?
#dictCounterNames[1526495508] = 'regulation ?' # -500 -  -2500 ? # anticorrelation with 1526466858, 1526467213, 1526471371

# remote counter
#dictCounterNames[1526469030] = 'Batt laden2'
#dictCounterNames[1532951436] = 'PV2 ?'

# remotesensor
#dictCounterNames[1526468849] = 'remotesensor ?'
#dictCounterNames[1526468909] = 'remotesensor ?' # const 3000
#dictCounterNames[1526471294] = 'PowerFactor ?'


strBasedir = '/home/friso/src/EMS-Readout/Testdata/FileDB/'


### for debugging only
#dictCounterNames.clear()
#dictCounterNames[1526466858] = 'Überschuss CGout[W]'



lstLegend = []

#for strBCFile in fnBusCounter:
#    ms = re.match('.*counter_(\d*)_global_(\d*)_(\d*)_(\d*).txt',strBCFile)
#    BcId = int(ms[1])

#for globbing
strYear = '2020'
strMonth = '11'
strDay = '21'

# for all registered counters
for CounterId in dictCounterNames.keys():
    lstDataCounter = []
    CounterName = dictCounterNames[CounterId]
    lstLegend.append(str(CounterId)+'  '+CounterName)
    allFilesForCounter = glob.glob(strBasedir+strYear+'/Linear/*'+str(CounterId)+'_global_'+strMonth+'_'+strDay+'_'+strYear+'.txt')

    # for all date-files
    for strBCFile in allFilesForCounter:
        ms = re.match('.*(\d*)_global_(\d*)_(\d*)_(\d*).txt',strBCFile)

        strDate=ms[4]+'-'+ms[2]+'-'+ms[3]
        print('BC: {} Name: {}  date: {}'.format(CounterId,CounterName,strDate))
        lstTupDay = []
        
        with open(strBCFile) as csvfile:
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
        lstDataCounter.extend(lstTupDay)
    #    last=0
    #    for tup in lstTup:
    #        t = tup[0]
    #        diff = t-last
    #        print('{}   {}'.format(t,diff))
    #        last=t
     #   print(lstTup[-1])
    data = np.array(lstDataCounter)
    plt.plot(data[:,1],data[:,2],'.')

plt.legend(lstLegend)
plt.show()
import datetime
import glob
import csv
import re
import numpy as np
import matplotlib.pyplot as plt


#%%
dictCounterNames = {}
# buscounter
dictCounterNames[1526658041] = 'Netzfrequzne [Hz]'
dictCounterNames[1526471785] = 'WP Bezug' # 0
dictCounterNames[1526466886] = 'Bezug' # 
dictCounterNames[1526466858] = 'Überschuss' # ? korreliert mit 1526467213 und 1526471371
# dictCounterNames[1526467140] = 'Heizstab Bezug' # 0

# calculation counter
#dictCounterNames[1526467264] = 'Bezug-HZ' # 0
#dictCounterNames[1526467826] = 'Bezug-HZ-ECAR' # 0 
#dictCounterNames[1526467678] = 'Überschuss+HZ+ECAR' # 0 
dictCounterNames[1526477230] = 'Gesamtverbrauch' # 0
dictCounterNames[1526467213] = 'Überschuss+HZ' # 500 - 2500
dictCounterNames[1526477645] = 'Hausstrom' # 0 
dictCounterNames[1526471371] = 'Überschuss+HZ+ECAR+Laden-Entlade' 
#dictCounterNames[1526477597] = 'Wärmestrom' # 0 
dictCounterNames[1526471474] = 'Bezug-HZ-ECAR-Discharge+Charge'


# regulation
dictCounterNames[1526495469] = 'BATT Power'
dictCounterNames[1526495508] = 'Grid Power'

# remote counter
dictCounterNames[1526469030] = 'BATT Laden'
dictCounterNames[1532951436] = 'PV DC Seitig'

# remotesensor
dictCounterNames[1526468849] = 'BATT V'
dictCounterNames[1526468909] = 'Max Laden' # const 3000
dictCounterNames[1526471294] = 'BATT A'
dictCounterNames[1526468812] = 'BATT Ladezustand'
dictCounterNames[1526468926] = 'Max Entladen'

# update names from file
#strFName='/home/friso/src/EMS-Readout/src/Name-mapping.txt'
#f = open(strFName)
#for line in f:
#    ms=re.match('.*_(\d*)_Name=(.*)',line)
#    if ms:
#        id = int(ms[1])
#        #print('ID: {} Name: {}'.format(id,ms[2]))
#        foundID=dictCounterNames.get(id)
#        if foundID:
#            dictCounterNames[id] = ms[2]


#for id in dictCounterNames.keys():
#    print('ID: {}  Name: {}'.format(id,dictCounterNames[id]))










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
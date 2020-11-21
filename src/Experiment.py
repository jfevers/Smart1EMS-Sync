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
# buscounter
dictCounterNames[1526658041] = 'Frequency [Hz]'
dictCounterNames[1526471785] = '?'
dictCounterNames[1526466886] = 'Bezug CGin [W]'
dictCounterNames[1526466858] = 'Überschuss CGout[W]'
dictCounterNames[1526467140] = '?'

# calculation counter
dictCounterNames[1526467264] = '?'
dictCounterNames[1526467826] = '?'
dictCounterNames[1526467678] = '?'
dictCounterNames[1526477230] = '?'
dictCounterNames[1526467213] = '?'
dictCounterNames[1526477645] = '?'
dictCounterNames[1526471371] = '?'
dictCounterNames[1526477597] = '?'
dictCounterNames[1526471474] = 'Batt laden [W]'

strBasedir = '/home/friso/src/EMS-Readout/Testdata/FileDB/'

fnBusCounter = glob.glob(strBasedir+'2020/Linear/buscounter*_global_11_21_2020.txt')
fnCalcCounter = glob.glob(strBasedir+'2020/Linear/calculationcounter*_global_11_21_2020.txt')

lstLegend = []

for strBCFile in fnCalcCounter:
    ms = re.match('.*counter_(\d*)_global_(\d*)_(\d*)_(\d*).txt',strBCFile)
    BcId = int(ms[1])

#    if BcId != 1526471474:
#        continue

    strDate=ms[4]+'-'+ms[2]+'-'+ms[3]
    print('BC: {}  date: {}'.format(BcId,strDate))
    if dictCounterNames.get(BcId):
        lstLegend.append(str(BcId)+'  '+dictCounterNames[BcId])
    else:
        lstLegend.append(str(BcId)+'  unknown')
    lstTup = []
    
    with open(strBCFile) as csvfile:
        reader = csv.reader(csvfile,delimiter=';')
        for row in reader:
            strTS = row[0] # read timestamp
            intTS = int(strTS)
            strValue = row[1]
            DT = datetime.datetime.fromtimestamp(int(strTS))  
            fVal = float(strValue)
            lstTup.append((intTS,fVal))
            # print('     strDT: {}  dt: {}   value: {}'.format(strTS,DT,fVal))
    lstTup.sort(key=lambda tup: tup[0])

#    last=0
#    for tup in lstTup:
#        t = tup[0]
#        diff = t-last
#        print('{}   {}'.format(t,diff))
#        last=t

    data = np.array(lstTup)
    plt.plot(data[:,0],data[:,1])

plt.legend(lstLegend)
plt.show()
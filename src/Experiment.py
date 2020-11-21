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

dictBCNames = {}

dictBCNames[1526658041] = 'Frequency'
dictBCNames[1526471785] = '?'
dictBCNames[1526466886] = '[kW]'
dictBCNames[1526466858] = '[kW]'
dictBCNames[1526467140] = '?'


strBasedir = '/home/friso/src/EMS-Readout/Testdata/FileDB/'

rawBusCounter = glob.glob(strBasedir+'2020/Linear/buscounter*_global_11_20_2020.txt')

for strBCFile in rawBusCounter:
    ms = re.match('.*buscounter_(\d*)_global_(\d*)_(\d*)_(\d*).txt',strBCFile)
    BcId = int(ms[1])
    strDate=ms[4]+'-'+ms[2]+'-'+ms[3]
    print('BC: {}  date: {}'.format(BcId,strDate))
    if BcId != 1526467140:
        continue

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
#    for tup in lstTup:
#        print('{}   {}'.format(tup[0],tup[1]))
    data = np.array(lstTup)
    plt.plot(data[:,0],data[:,1])
    plt.show()
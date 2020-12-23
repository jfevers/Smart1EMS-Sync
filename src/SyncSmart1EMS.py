import ServiceAppClass
import logging
import time
import configparser
import os
import sys
import datetime
import XmlRpc2Mqtt
import TransferCounter




def str2Bool(strStr):
    res = False
    if strStr.lower() == 'true':
        res = True
    return res



class SyncSmart1EMS(ServiceAppClass.ServiceAppClass):

    @staticmethod
    def registerConfigEntries(config):
        XmlRpc2Mqtt.XmlRpc2Mqtt.registerConfigEntries(config)
        TransferCounter.TransferCounter.registerConfigEntries(config)
        config['SyncSmart1EMS'] = {
        'sync-counter': 'False',
        'loglevel': 'INFO'
        }



    def __init__(self):
        super().__init__(self.registerConfigEntries, "SyncSmart1EMS")
        self.myXml2Mqtt = XmlRpc2Mqtt.XmlRpc2Mqtt(self.config)            
        self.myTrfCntr = TransferCounter.TransferCounter(self.config)            
        self.myXml2Mqtt.describeChannels()
        self.bSyncCounter = str2Bool(self.config['SyncSmart1EMS']['sync-counter'])
        strLogLevel = self.config['SyncSmart1EMS']['loglevel']
        logging.info('Setting loglevel to '+strLogLevel)
        logging.getLogger().setLevel(strLogLevel)



    def run(self):
        if self.bSyncCounter:
            logging.info("Preparing TransferCounter")
            self.myTrfCntr.checkAndPrepareDirectories()

        self.bKeepRunning = True
        tLast = datetime.datetime.now()-datetime.timedelta(seconds=60)
        tLastHourly = tLast.hour
        tLastDay = tLast.day
        while self.bKeepRunning:
            tNow = datetime.datetime.now()
            tDiff = (tNow-tLast).total_seconds()
            if tDiff >= 10:
                logging.debug('Calling XmlRpc..')
                self.myXml2Mqtt.processAll()
                tLast = tNow
            time.sleep(2)

            if self.bSyncCounter:
                bUpdateDB = False
                # evers full hour get files from today
                if tNow.hour > tLastHourly and  tNow.minute == 0:
                    logging.info('Hourly sync of files today')
                    tLastHourly = tNow.hour
                    self.myTrfCntr.updateFiles(numDaysBack=0)
                    bUpdateDB = True
                # every midnight get last file changes from yesterday
                if tNow.day > tLastDay and tNow.hour == 0 and tNow.minute == 1:
                    logging.info('Daily sync of files from yesterday')
                    tLastDay = tNow.day
                    tLastHourly = tNow.hour
                    self.myTrfCntr.updateFiles(numDaysBack=1)
                    bUpdateDB = True
                if bUpdateDB:
                    self.myTrfCntr.updateAllCounter() # insert into DB
        self.myXml2Mqtt.cleanUp()


#### main ###


myService = SyncSmart1EMS()
myService.run()






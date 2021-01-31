import ServiceAppClass
import logging
import time
import configparser
import os
import sys
import datetime
import XmlRpc2Mqtt
import CtrToDB
import SumsToDB
import TransferFiles




def str2Bool(strStr):
    res = False
    if strStr.lower() == 'true':
        res = True
    return res



class SyncSmart1EMS(ServiceAppClass.ServiceAppClass):

    @staticmethod
    def registerConfigEntries(config):
        XmlRpc2Mqtt.XmlRpc2Mqtt.registerConfigEntries(config)
        TransferFiles.TransferFiles.registerConfigEntries(config)
        CtrToDB.CtrToDB.registerConfigEntries(config)
        # remove duplicate entry of data-dir before __init__
        #del config['TransferCounter']['DataDir']
        config['SyncSmart1EMS'] = {
        'sync-counter': 'False',
        'loglevel': 'INFO'
        }



    def __init__(self):
        super().__init__(self.registerConfigEntries, "SyncSmart1EMS")
        self.myXml2Mqtt = XmlRpc2Mqtt.XmlRpc2Mqtt(self.config)            
        self.myTrfFiles = TransferFiles.TransferFiles(self.config)            
        # re-add datadir as reference
        self.config['CtrToDB']['DataDir'] = self.config['TransferFiles']['DataDir']
        self.myTrfCntr = CtrToDB.CtrToDB(self.config)            
        self.myTrfSums = SumsToDB.SumsToDB(self.config)         

        self.myXml2Mqtt.describeChannels()
        self.bSyncCounter = str2Bool(self.config['SyncSmart1EMS']['sync-counter'])
        strLogLevel = self.config['SyncSmart1EMS']['loglevel']
        logging.info('Setting loglevel to '+strLogLevel)
        logging.getLogger().setLevel(strLogLevel)



    def run(self):
        if self.bSyncCounter:
            logging.info("Preparing TransferFile, CtrToDB and SumsToDB")
            self.myTrfFiles.checkAndPrepareDirectories()
            logging.info("Initial sync of all files")
            self.myTrfFiles.updateFiles(bAll=True) # one complete file sync on start-up

            # check if checkAndPrepareDirectories() was an initial run
            if self.myTrfFiles.getResetTables(): 
                logging.info("running first big update for all counters")
                self.myTrfCntr.clearCounterTables()
                self.myTrfCntr.readIdMapping()
                self.myTrfCntr.updateIdMapping()
                self.myTrfCntr.bBatchMode = True
                self.myTrfCntr.updateAllCounter()
                self.myTrfSums.updateAllSums()
                self.myTrfCntr.bBatchMode = False
                # TODO reset Sums
            else:
                self.myTrfCntr.readIdMappingFromDB()
                self.myTrfSums.readIdMappingFromDB()
                self.myTrfCntr.updateAllCounter()
                self.myTrfSums.updateAllSums()

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
                try: 
                    bUpdateDB = False
                    # evers full hour get files from today
                    if (tNow.hour > tLastHourly and  tNow.minute == 0):
                        logging.info('Hourly sync of files today')
                        tLastHourly = tNow.hour
                        self.myTrfFiles.updateFiles(numDaysBack=0)
                        bUpdateDB = True
                    # every midnight get last file changes from yesterday
                    if tNow.day > tLastDay and tNow.hour == 0 and tNow.minute == 1:
                        logging.info('Daily sync of files from yesterday')
                        tLastDay = tNow.day
                        tLastHourly = tNow.hour
                        self.myTrfFiles.updateFiles(numDaysBack=1)
                        bUpdateDB = True
                    if bUpdateDB:
                        self.myTrfCntr.updateAllCounter() # insert into DB
                        self.myTrfSums.updateAllSums()

                except Exception as e:
                    logging.error("TransferCounter failed: {}".format(e))
                    logging.error("disabling SyncCounter for now")
                    self.bSyncCounter = False
        self.myXml2Mqtt.cleanUp()


#### main ###


myService = SyncSmart1EMS()
myService.run()






import ServiceAppClass
import logging
import time
import configparser
import os
import sys
import datetime
import XmlRpc2Mqtt
import TransferCounter






class SyncSmart1EMS(ServiceAppClass.ServiceAppClass):

    @staticmethod
    def registerConfigEntries(config):
        XmlRpc2Mqtt.XmlRpc2Mqtt.registerConfigEntries(config)
        TransferCounter.TransferCounter.registerConfigEntries(config)



    def __init__(self):
        super().__init__(self.registerConfigEntries, "SyncSmart1EMS")
        self.myXml2Mqtt = XmlRpc2Mqtt.XmlRpc2Mqtt(self.config)            
        self.myTrfCntr = TransferCounter.TransferCounter(self.config)            
        self.myXml2Mqtt.describeChannels()


    def run(self):
        self.bKeepRunning = True
        tLast = datetime.datetime.now()-datetime.timedelta(seconds=60)

        while self.bKeepRunning:
            tNow = datetime.datetime.now()
            tDiff = (tNow-tLast).total_seconds()
            if tDiff >= 10:
                logging.debug('Calling XmlRpc..')
                self.myXml2Mqtt.processAll()
                tLast = tNow
            time.sleep(2)


        self.myXml2Mqtt.cleanUp()


#### main ###


myService = SyncSmart1EMS()
myService.run()






import ServiceAppClass
import XmlRpc2Mqtt
import time

class TestXml2Mqtt(ServiceAppClass.ServiceAppClass):
    '''
    Just read config file, or generate a template, and create instance to test
    '''
    def __init__(self):
        super().__init__(XmlRpc2Mqtt.XmlRpc2Mqtt.registerConfigEntries, "XmlRpc2Mqtt")        
        self.myUpdater = XmlRpc2Mqtt.XmlRpc2Mqtt(self.config)            

    def run(self):
        self.myUpdater.describeChannels()
        nCount = 0
        bKeepRunning = True
        while bKeepRunning:
            self.myUpdater.processAll()
            time.sleep(10)
            if nCount >10:
                bKeepRunning = False
            nCount += 1

        self.myUpdater.cleanUp()


#### main ###

myTester = TestXml2Mqtt()
myTester.run()






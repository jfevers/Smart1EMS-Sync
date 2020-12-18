import logging
import XmlRpc2Mqtt
import time
import configparser
import os


class TestXml2Mqtt:
    '''
    Just read config file, or generate a template, and create instance to test
    '''
    def __init__(self):
        self.myDir = os.path.dirname(os.path.realpath(__file__))
        logging.basicConfig(format='%(asctime)s  %(levelname)s: %(message)s', level=logging.DEBUG)

        conffilename = self.myDir+"/XmlRpc2Mqtt.conf"
        print('Using config file: '+conffilename)
        config = configparser.ConfigParser()

        XmlRpc2Mqtt.XmlRpc2Mqtt.registerConfigEntries(config)

        if os.path.isfile(conffilename):
            config.read(conffilename)
        else:
            print('Wrote example config file: {}'.format(conffilename))
            with open(conffilename, 'w') as configfile:
                config.write(configfile)
            exit(1)
        self.myUpdater = XmlRpc2Mqtt.XmlRpc2Mqtt(config)            

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


#XmlAddr = 'http://10.0.0.4:20000/'
#Password = 'w9tknp7ibc'
#MqttAddr = "gelbekiste"



#### main ###
myTester = TestXml2Mqtt()
myTester.run()






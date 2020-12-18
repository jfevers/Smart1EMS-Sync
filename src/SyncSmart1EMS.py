import logging
import Xml2Mqtt


logging.basicConfig(format='%(asctime)s  %(levelname)s: %(message)s', level=logging.DEBUG)


bKeepRunning = True

myApp = Xml2Mqtt.XmlRpc2Mqtt() # set global pointer so call-basks can call into this instance
logging.info("starting XML2Mqtt service")

myApp.describeChannels()

def sigTerm(signum, frame):
    global bKeepRunning
    logging.warning('Received SIGINT or SIGTERM, going down')
    bKeepRunning = False


signal.signal(signal.SIGTERM, sigTerm)
signal.signal(signal.SIGINT, sigTerm)


while bKeepRunning:
    myApp.processAll()
    time.sleep(10)

myApp.cleanUp()
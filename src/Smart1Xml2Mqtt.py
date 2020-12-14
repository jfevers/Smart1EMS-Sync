import xmlrpc.client
import logging
import paho.mqtt.client as mqtt
import time
import json
import datetime
import signal

myApp = 0
bKeepRunning = True


# global call-back for MQTT-client, called when connection is established
def mqtt_onConnect(client, userdata, flags, rc):
    if rc==0:
        logging.info("connected to MQTT, Returned code={}".format(rc))
    else:
        logging.info("Bad connection Returned code={}".format(rc))


# global call-back for MQTT-client, called when a subscription is updated.
# This global function calls back into the one and only instance of the class
def mqtt_onMessage(client, userdata, message):
    global myApp
    strMsg = str(message.payload.decode("utf-8"))
    logging.info("mqtt "+message.topic+" received: "+strMsg)
    myApp.mqttOnMessage(client,userdata,message)



def sigTerm(signum, frame):
    global bKeepRunning
    logging.warning('Received SIGINT or SIGTERM, going down')
    bKeepRunning = False




class Smart1XmlRpc2Mqtt:
    """
    """
    def __init__(self):
        self.strXmlAddr = 'http://10.0.0.4:20000/'
        self.strPassword = 'w9tknp7ibc'
        self.strMqttAddr = "gelbekiste"
        self.mqttClient = mqtt.Client("Smart1-EMS")
        self.strTopicBase = "Smart1-EMS/"
    
        self.XmlRpcProxy = xmlrpc.client.ServerProxy(self.strXmlAddr)
        self.mqttClient.on_connect = mqtt_onConnect
        self.mqttClient.on_message = mqtt_onMessage
        self.mqttClient.connect(self.strMqttAddr)
        self.mqttClient.loop_start()  #Start loop 
#        self.mqttClient.subscribe(self.strMTopicSetCapture)
        # dictXmlResult = self.XmlRpcProxy.getDeviceInfo(self.strPassword)


    def describeChannels(self):
        try:
            dictXmlResult = self.XmlRpcProxy.getAllCurrentLinearValues(self.strPassword)
            dictSensors = dictXmlResult['Reply']
            for senid in dictSensors.keys():
                sen = dictSensors[senid]
                logging.info(senid+'   '+sen['Name']+":  "+sen['Current_Value'])
        except Exception as exc:
            logging.error('failed to query Smart1-EMS on {}: {}'.format(self.strXmlAddr,exc))




    def processXmlLinears(self):
        dictXmlResult = self.XmlRpcProxy.getAllCurrentLinearValues(self.strPassword)
        dictSensors = dictXmlResult['Reply']
        resCode = dictXmlResult['ErrorCode']
        if resCode == 0:
            strRes = 'OK'
        else:
            strRes = dictXmlResult['ErrorString']

        if resCode == 0:
            for senid in dictSensors.keys():
                sen = dictSensors[senid]
                topic = self.strTopicBase + senid
                self.mqttClient.publish(topic,json.dumps(sen))
        return strRes


    def processXmlPV(self,):
        dictXmlResult = self.XmlRpcProxy.getPhotovoltaicConfiguration(self.strPassword)
        dictReply = dictXmlResult['Reply']
        resCode = dictXmlResult['ErrorCode']
        if resCode == 0:
            strRes = 'OK'
        else:
            strRes = dictXmlResult['ErrorString']

        if resCode == 0:
            dictInverters = dictReply['Inverters']
            for invid in dictInverters.keys():
                inv = dictInverters[invid]
                topic = self.strTopicBase + invid
                self.mqttClient.publish(topic,json.dumps(inv))
            dictMF = dictReply['Modulfields']
            for mfid in dictMF.keys():
                mf = dictMF[mfid]
                topic = self.strTopicBase + mfid
                self.mqttClient.publish(topic,json.dumps(mf))
        return strRes




    def processAll(self):
        strNow = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            strRes = self.processXmlLinears()
            strRes = self.processXmlPV()
            self.mqttClient.publish(self.strTopicBase + 'last_result',strRes)
            self.mqttClient.publish(self.strTopicBase + 'last_update',strNow)
        except Exception as exc:
            strMsg = 'failed to query Smart1-EMS on {}: {}'.format(self.strXmlAddr,exc)
            logging.error(strMsg)
            self.mqttClient.publish(self.strTopicBase + 'last_result',strMsg)
            self.mqttClient.publish(self.strTopicBase + 'last_update',strNow)





    def mqttOnMessage(self,client, userdata, message):
        strMsg = str(message.payload.decode("utf-8")).upper()
#        if message.topic == self.strMTopicSetCapture and strMsg == "ON":
#            myApp.myImgHandler.setCapture(True) 
#        if message.topic == self.strMTopicSetCapture and strMsg == "OFF":
#            myApp.myImgHandler.setCapture(False) 
#        if message.topic == self.strMTopicSetExpRef:
#            self.cam.setExpReference(int(strMsg))
#        if message.topic == self.strMTopicSetIntervalVid:
#            tInt = int(strMsg)
#            self.myImgHandler.setIntervals(tInt, self.myImgHandler.tIntervalImg)
#            if tInt <15:
#                self.tSleep = 1
#            else:
#                self.tSleep = 10
#        if message.topic == self.strMTopicSetIntervalImg:
#            self.myImgHandler.setIntervals( self.myImgHandler.tIntervalVid, int(strMsg))



    def cleanUp(self):
            logging.info("End of mainloop, cleaning-up")
            self.mqttClient.publish(self.strTopicBase + 'last_result', "Service terminated")
            time.sleep(2)
            self.mqttClient.loop_stop()    #Stop mqtt loop 
            logging.info("END")



logging.basicConfig(format='%(asctime)s  %(levelname)s: %(message)s', level=logging.DEBUG)




myApp = Smart1XmlRpc2Mqtt() # set global pointer so call-basks can call into this instance
logging.info("starting XML2Mqtt service")

myApp.describeChannels()


signal.signal(signal.SIGTERM, sigTerm)
signal.signal(signal.SIGINT, sigTerm)


while bKeepRunning:
    myApp.processAll()
    time.sleep(10)

myApp.cleanUp()
import logging
import configparser
import os
import sys
import signal



class ServiceAppClass:

    # static reference to single instance
    myApp = 0

    @staticmethod
    def sigTerm_(signum, frame):
        logging.warning('Received SIGINT or SIGTERM, going down')
        ServiceAppClass.myApp.stop()

    @staticmethod
    def sigUsr1_(signum, frame):
        logging.warning('Received SIGUSR1')
        ServiceAppClass.myApp.sigUsr1()

    def sigUsr1(self):
        logging.info('ServiceAppClass.sigUsr1(): doing nothing')

    def stop(self):
        self.bKeepRunning = False



    '''
    Just read config file, or generate a template, 
    '''
    def __init__(self, fnctRegisterConfig, strAppName):
        if self.myApp != 0:
            raise Exception("Only one instance possible")
        ServiceAppClass.myApp = self

        signal.signal(signal.SIGTERM, ServiceAppClass.sigTerm_)
        signal.signal(signal.SIGINT, ServiceAppClass.sigTerm_)
        signal.signal(signal.SIGUSR1, ServiceAppClass.sigUsr1_)

        logging.basicConfig(format='%(asctime)s  %(levelname)s: %(message)s', level=logging.DEBUG)
        if len(sys.argv)<2:
            logging.error("Usage: "+strAppName+" <config_dir_path>")
            exit(1)
        strConfFileName = sys.argv[1]+"/"+strAppName+".conf"
        logging.info('Using config file: '+strConfFileName)
        self.config = configparser.ConfigParser()

        fnctRegisterConfig(self.config)

        if os.path.isfile(strConfFileName):
            self.config.read(strConfFileName)
            with open(strConfFileName+'.new', 'w') as configfile:
                self.config.write(configfile)
        else:
            print('Wrote example config file: {}'.format(strConfFileName))
            with open(strConfFileName, 'w') as configfile:
                self.config.write(configfile)
            exit(1)

    

    def run(self):
        raise Exception("Must overwrite this method")
      



import TransferCounter
import configparser
import os

class TestTransferCounter:
    def __init__(self):
        self.myDir = os.path.dirname(os.path.realpath(__file__))

        conffilename = self.myDir+"/TransferCounter.conf"
        print('Using config file: '+conffilename)
        config = configparser.ConfigParser()

        TransferCounter.TransferCounter.registerConfigEntries(config)

        if os.path.isfile(conffilename):
            config.read(conffilename)
        else:
            print('Wrote example config file: {}'.format(conffilename))
            with open(conffilename, 'w') as configfile:
                config.write(configfile)
            exit(1)
        self.myUpdater = TransferCounter.TransferCounter(config)            

    def run(self):

#        bYesterday = False
#        opts, argv = getopt.getopt(sys.argv[1:], "y")
#        for k, v in opts:
#            if k == '-y':
#                bYesterday = True

#        self.myUpdater.updateFiles(bAll=True)
#        self.myUpdater.updateFiles(numDaysBack=0) # today only
#        self.myUpdater.updateFiles(numDaysBack=1) # yesterday only
        self.myUpdater.readIdMapping()
        self.myUpdater.updateIdMapping() # do not update every time
        #self.myUpdater.clearCounterTables() # just to start over completely
        #self.myUpdater.updateAllCounter()





#### main ###
myTester = TestTransferCounter()
myTester.run()

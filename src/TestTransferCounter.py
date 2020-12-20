import ServiceAppClass
import TransferCounter

class TestTransferCounter(ServiceAppClass.ServiceAppClass):

    def __init__(self):
        super().__init__(TransferCounter.TransferCounter.registerConfigEntries, "TransferCounter")
        self.myUpdater = TransferCounter.TransferCounter(self.config)            



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
        self.myUpdater.updateAllCounter()





#### main ###
myTester = TestTransferCounter()
myTester.run()

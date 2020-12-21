import ServiceAppClass
import TransferCounter

class TestTransferCounter(ServiceAppClass.ServiceAppClass):

    def __init__(self):
        super().__init__(TransferCounter.TransferCounter.registerConfigEntries, "TransferCounter")
        self.myUpdater = TransferCounter.TransferCounter(self.config)            



    def run(self):

        self.myUpdater.checkAndPrepareDirectories()
        self.myUpdater.updateFiles(numDaysBack=1) # yesterday only
        self.myUpdater.updateFiles(numDaysBack=0)
        #self.myUpdater.clearCounterTables() # just to start over completely
        self.myUpdater.updateAllCounter()





#### main ###
myTester = TestTransferCounter()
myTester.run()

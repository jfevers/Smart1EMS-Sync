import ServiceAppClass
import TransferSums

class TestTransferSums(ServiceAppClass.ServiceAppClass):

    def __init__(self):
        super().__init__(TransferSums.TransferSums.registerConfigEntries, "TransferCounter")
        self.myUpdater = TransferSums.TransferSums(self.config)            



    def run(self):
        self.myUpdater.readIdMappingFromDB()
       # self.myUpdater.dictCounterNames[1526476967]  = 'Eigenverbrauch' # just debug one counter
        self.myUpdater.updateAllSums()



#### main ###
myTester = TestTransferSums()
myTester.run()

import ServiceAppClass
import TransferFiles

class TestTransferFiles(ServiceAppClass.ServiceAppClass):

    def __init__(self):
        super().__init__(TransferFiles.TransferFiles.registerConfigEntries, "TestTransferFiles")
        self.myTC = TransferFiles.TransferFiles(self.config)            



    def run(self):

        self.myTC.checkAndPrepareDirectories()
        #self.myTC.updateFiles(bAll=True) # yesterday only
        self.myTC.updateFiles(numDaysBack=0)
#        self.myTC.updateErrorLog()




#### main ###
myTester = TestTransferFiles()
myTester.run()

import ServiceAppClass
import SumsToDB

class TestSumsToDB(ServiceAppClass.ServiceAppClass):

    def __init__(self):
        super().__init__(SumsToDB.SumsToDB.registerConfigEntries, "TestCtrToDB")
        self.myUpdater = SumsToDB.SumsToDB(self.config)            



    def run(self):
        self.myUpdater.readIdMappingFromDB()
       # self.myUpdater.dictCounterNames[1526476967]  = 'Eigenverbrauch' # just debug one counter
        self.myUpdater.updateAllSums()



#### main ###
myTester = TestSumsToDB()
myTester.run()

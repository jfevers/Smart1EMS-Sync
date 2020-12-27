import ServiceAppClass
import CtrToDB

class TestCtrToDB(ServiceAppClass.ServiceAppClass):

    def __init__(self):
        super().__init__(CtrToDB.CtrToDB.registerConfigEntries, "TestCtrToDB")
        self.myTC = CtrToDB.CtrToDB(self.config)            



    def run(self):
        self.myTC.readIdMappingFromDB()
        self.myTC.updateIdMapping() # do not update every time
#        self.myTC.dictCounterNames[1526476967]  = 'Eigenverbrauch' # just debug one counter
#        self.myTC.clearCounterTables() # just to start over completely
        self.myTC.updateAllCounter()





#### main ###
myTester = TestCtrToDB()
myTester.run()

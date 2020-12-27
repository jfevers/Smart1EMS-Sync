import ServiceAppClass
import LogToDB

class TestLogToDB(ServiceAppClass.ServiceAppClass):

    def __init__(self):
        super().__init__(LogToDB.LogToDB.registerConfigEntries, "TestCtrToDB")
        self.myUpdater = LogToDB.LogToDB(self.config)            



    def run(self):
        self.myUpdater.clearLogTable()
        self.myUpdater.prepareLogTable()
        self.myUpdater.decode()



#### main ###
myTester = TestLogToDB()
myTester.run()

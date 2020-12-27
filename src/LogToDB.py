import sqlite3
import datetime
import dateutil.tz
import CtrToDB

class LogToDB(CtrToDB.CtrToDB):



    def prepareLogTable(self):
        strTabN = 'Log'
        self.openDB()    
        strCmd = "select table_name from information_schema.tables where table_schema='EMSdata' and table_name='{}'".format(strTabN)
        self.mycursor.execute(strCmd)
        myresult = self.mycursor.fetchall()
        if len(myresult) == 0:
            strCmd = "CREATE TABLE {} (id int, time datetime, addr int, bus int,"\
            "errType int, errCode int, msg varchar(255), actionTaken varchar(255), "\
            "actionUndo varchar(255), acked varchar(10), statusType int, component varchar(255), "\
            "sensorCount varchar(255), PRIMARY KEY(id))".format(strTabN)
            self.mycursor.execute(strCmd)
        self.closeDB()

    def clearLogTable(self):
        self.openDB()
        self.mycursor.execute("DROP TABLE IF EXISTS Log")
        self.closeDB()



    def decode(self):
        self.strLogFileName = self.strDataDir+'/smart1.sqlite'
        self.dbLog = sqlite3.connect(self.strLogFileName)
        self.cursorLog = self.dbLog.cursor()
        strCmd = 'select * from alerts'
        self.cursorLog.execute(strCmd)
        myresult = self.cursorLog.fetchall()       
        self.dbLog.close()

#     0           ALERTID     INTEGER          
#     1           TIMEST      INTEGER          
#     2           ADDRESS     INTEGER          
#     3           BUS         INTEGER          
#     4           ERROR_TYPE  INTEGER          
#     5           ERRORCODE   INTEGER          
#     6           ALERT_DATA  TEXT             
#     7           ACTIONS_TA  TEXT             
#     8           ACTIONS_UN  TEXT             
#     9           ACKNOWLEDG  TEXT             
#     10          STATUSTYPE  INTEGER          
#     11          COMPONENT   TEXT             
#     12          SENSORCOUN  TEXT       
        self.openDB()
        for row in myresult:
            id = row[0]
            dt = datetime.datetime.utcfromtimestamp(row[1])  
            #works as expected even inside container
            dtUtc = dt.astimezone(dateutil.tz.tzutc())
            strUtc = dtUtc.strftime('%Y-%m-%d %H:%M:%S')
            iAddress = row[2]
            iBus = row[3]
            iErrorType = row[4]
            iErrorCode = row[5]
            strAlertData = row[6]
            strActionsTa = row[7]
            strActionsUn = row[8]
            strAck = row[9]
            iStatusType = row[10]
            strComponent = row[11]
            strSensorCount = row[12]
            print(row)
            strCmd = "INSERT INTO Log (id , time, addr, bus,"\
            "errType, errCode, msg, actionTaken , "\
            "actionUndo, acked, statusType, component, "\
            "sensorCount) VALUES (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\')"\
                .format(id,strUtc,row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12])
            self.mycursor.execute(strCmd)
        self.closeDB()




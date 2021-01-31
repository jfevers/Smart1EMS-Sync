import logging
import datetime
import os

class TransferFiles:

    @staticmethod
    def registerConfigEntries(config):
        config['TransferFiles'] = {
            'DataDir': '/my/data/tmp/dir',
            'Ems-address':'name_or_ip_of_EMS',
            'SSH-ID': 'id_or_file_with_priv_key',
            }


    def __init__(self,config):
        self.strDataDir = config['TransferFiles']['DataDir']
        self.strSshId = config['TransferFiles']['SSH-ID']
        self.strEmsAddr=config['TransferFiles']['ems-address']
        self.strScpBase = "scp -r -o \"KexAlgorithms +diffie-hellman-group1-sha1\" -o StrictHostKeyChecking=no -i {} root@{}:/Smart1".format(self.strSshId,self.strEmsAddr)
        self.bResetTables = False

    def getResetTables(self):
        return self.bResetTables



    def updateFiles(self, bAll=False, numDaysBack=0): 
        logging.debug("updateFiles()")
#        strRedirectStdout = " >>{}/FileCopy.log".format(self.strDataDir)
        strRedirectStdout = ""
        strTargetDir = self.strDataDir+"/FileDB"

        with open("{}/FileCopy.log".format(self.strDataDir),'a+') as f:
            f.write("{} updateFiles(bAll={}, numDaysBack={})\n".format(datetime.datetime.now().isoformat(),bAll, numDaysBack))

        if bAll:
        # complete history
            strCmd = self.strScpBase + "/FileDB/* {}/".format(strTargetDir)
            res = os.system(strCmd + strRedirectStdout)
            if res != 0:
                raise Exception("Command failed: "+strCmd)
        else:
            useDate = datetime.date.today()
            useDate = useDate- datetime.timedelta(days=numDaysBack)
            # only one day
            strPattern = "*global_{}_{}_{}.txt".format(useDate.month,useDate.day,useDate.year)
                # copy buscounter, calculationcounter, ... from Linear/
            strCmd = self.strScpBase + "/FileDB/{}/Linear/{} {}/{}/Linear/".format(useDate.year,strPattern,strTargetDir,useDate.year)
            res = os.system(strCmd + strRedirectStdout)
            if res != 0:
                raise Exception("Command failed: "+strCmd)

            lstSubDirs =["B1_A5_S1","B2_A1_S1","B2_A1_S2"] 
            for strSd in lstSubDirs:
                # copy raw bus counter data
                strCmd = self.strScpBase + "/FileDB/{}/{}/{}  {}/{}/{}".format(useDate.year,strSd,strPattern,strTargetDir,useDate.year,strSd)
                res = os.system(strCmd + strRedirectStdout)
                if res != 0:
                    logging.error("Command failed, but ignoring: "+strCmd)
                    #raise Exception("Command failed: "+strCmd)

    def updateErrorLog(self):
        strCmd = self.strScpBase + "/smart1.sqlite {}/".format(self.strDataDir)
        res = os.system(strCmd)
        if res != 0:
            raise Exception("Command failed: "+strCmd)


    def checkAndPrepareDirectories(self):
        strTarget1 = self.strDataDir+"/FileDB"
        if not os.path.isdir(strTarget1):
            os.mkdir(strTarget1)

        strInitalSyncDone = self.strDataDir+"/InitialSyncDone.txt"
        self.strNameFile = self.strDataDir+"/Name-mapping.txt"

        if not os.path.isfile(strInitalSyncDone):
            logging.info("Did not found {}, resetting DB and init from EMS completely".format(strInitalSyncDone))
            with open(strInitalSyncDone,"w") as f:
                f.write(datetime.datetime.now().isoformat())
            self.updateFiles(bAll=True)
            self.bResetTables = True
            bRunFirstFlush = True

        # prepare name-mapping file and read it  
        if not os.path.isfile(self.strNameFile):
            strCmd = self.strScpBase + "/smart1.conf {}/".format(self.strDataDir)
            logging.debug("cmd: "+strCmd)
            res = os.system(strCmd)
            if res != 0:
                raise Exception("Command failed: "+strCmd)
            strCmd = "grep Name {}/smart1.conf > {}".format(self.strDataDir,self.strNameFile)
            res = os.system(strCmd)
            if res != 0:
                raise Exception("Command failed: "+strCmd)


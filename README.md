# Project Goal
This project aims to read out data from an Energy Management System (EMS) from german company named "Smart1". This device can be found in e.g. battery systems called "GreenRock" from austrian company "BlueSky".

My motivation is to get live values into my home automation (OpenHAB2) and to safely store energy data in a database to analyse it with Grafana for example. All this without any cloud software from third parties. (It is my device, so it is my data.)

# Structure and Status
The project consist of two different building blocks:
- XmlRpc2Mqtt: Call the well-defined XML-RPC-API on TCP port 20000 and send that data as JSON to your own MQTT broker. Useful subscrbe from any home automation like FHEM, OpenHAB, Node-Red, ...
- TransferCounter: Download intern statistic files (CSV as FileDB) and insert them into MariaDB, MySQL, ...

The service SyncSmart1EMS put both parts together and runs them in background, ideally as docker container.
The current state is, that both parts are integrated, but an encoding issue blocks the TransferCounter part. XmlRpc2Mqtt works reliable inside the container.


# Todos:
- Transfercounter: infere time range to sync backwards automatically
- TransferCounter: integrate longterm-statistics
- Document setup procedure

# OpenHAB
## Thing
Add the following into your MQTT-setup (adapt appropriatly, of course):

    Thing mqtt:topic:myBroker:Smart1Ems "Smart1 EMS" {
        Channels:
            Type string : EmsLastUpdate "EMS last update"   [stateTopic="Smart1-EMS/last_update"]
            Type string : EmsLastResult "EMS last result"   [stateTopic="Smart1-EMS/last_result"]
            Type string : EmsPVSum      "PV Summe"          [stateTopic="Smart1-EMS/pv_global_1526476850"]
            Type string : EmsPwrSelf    "Eigenverbrauch"    [stateTopic="Smart1-EMS/arithmetic_1526476967"]
            Type string : EmsPwrOut     "Überschuss"        [stateTopic="Smart1-EMS/buscounter_1526466858"]
            Type string : EmsPwrIn      "Bezug"             [stateTopic="Smart1-EMS/buscounter_1526466886"]
            Type string : EmsPwrHouse   "Hausstrom"         [stateTopic="Smart1-EMS/calculationcounter_1526477645"]

            Type string : EmsInvWR1   "WR1"         [stateTopic="Smart1-EMS/Inverter_B2_A1"]
            Type string : EmsInvDC    "DC"          [stateTopic="Smart1-EMS/Inverter_B1_A5"]
    }

## Items

Because JSONPATH cannot decode from string to int, I have two items for each data point: One string and one number item. A rule is triggered by the string item, decoding the JSON into a number sending this number as update to the number item.

    String EmsLastUpdate "EMS Last update"                 (gAllEms)    {channel="mqtt:topic:myBroker:Smart1Ems:EmsLastUpdate"} 
    String EmsLastResult "EMS Last result"                 (gAllEms)    {channel="mqtt:topic:myBroker:Smart1Ems:EmsLastResult"} 

    String   EmsPVSumStr   "[%s]"                   (gAllEmsRaw) {channel="mqtt:topic:myBroker:Smart1Ems:EmsPVSum"} 
    String   EmsPwrSelfStr   "[%s]"  (gAllEmsRaw) {channel="mqtt:topic:myBroker:Smart1Ems:EmsPwrSelf"} 
    String   EmsPwrOutStr    "[%s]"   (gAllEmsRaw) {channel="mqtt:topic:myBroker:Smart1Ems:EmsPwrOut"} 
    String   EmsPwrInStr     "[%s]"    (gAllEmsRaw) {channel="mqtt:topic:myBroker:Smart1Ems:EmsPwrIn"} 
    String   EmsPwrHouseStr  "[%s]"    (gAllEmsRaw) {channel="mqtt:topic:myBroker:Smart1Ems:EmsPwrHouse"} 

    Number   EmsPVSum      "PV Gesamt [%d W]"   <sun_clouds>  (gAllEms)   
    Number   EmsPwrSelf    "Eigenverbrauch [%d W]"   <sun_clouds>  (gAllEms)   
    Number   EmsPwrOut     "Überschuss [%d W]"   <sun_clouds>  (gAllEms)   
    Number   EmsPwrIn      "Bezug [%d W]"   <sun_clouds>  (gAllEms)   
    Number   EmsPwrHouse   "Hausstrom [%d W]" (gAllEms)

    String EmsInvWR1Str   "WR1" {channel="mqtt:topic:myBroker:Smart1Ems:EmsInvWR1"}
    String EmsInvDCStr    "DC"  {channel="mqtt:topic:myBroker:Smart1Ems:EmsInvDC"}

    Number EmsWr1String1 "Wr1 #1 [%d W]" (gAllEms)
    Number EmsWr1String2 "Wr1 #2 [%d W]" (gAllEms)
    Number EmsWr1        "Wr1 Sum [%d W]" (gAllEms)
    Number EmsDcSeitig   "DC  #1 [%d W]" (gAllEms)

## Rules

    rule "DecodeJson"
    when 
        Member of gAllEmsRaw received update 
    then
        var String sDevName = triggeringItem.name.replace("Str","")

        val newValue = transform("JSONPATH", "$.Current_Value", triggeringItem.state.toString)
        //logInfo("EMS", sDevName+": "+newValue)
        val tempItem = ScriptServiceUtil.getItemRegistry.getItem(sDevName)
        // post the new value to the Number Item
        tempItem.postUpdate( newValue )
    end


    // sum up two items from two PV-strings to the combined load of the inverter
    rule "DecodeWr1"
    when
        Item EmsInvWR1Str received update
    then
        val PAC1 = Integer::parseInt(transform("JSONPATH", "$.String_1.PAC", triggeringItem.state.toString))
        val PAC2 = Integer::parseInt(transform("JSONPATH", "$.String_2.PAC", triggeringItem.state.toString))
        EmsWr1String1.postUpdate(PAC1)
        EmsWr1String2.postUpdate(PAC2)
        EmsWr1.postUpdate(PAC1+PAC2)
    end



# Setup
Prepare access to EMS (the router is the one in front of the EMS, not your internet access router):
- add TCP-forwarding inside router: 22 -> 192.168.1.184:22 (SSH)
- add TCP-forwarding inside router: 20000 -> 192.168.1.184:20000 (XML-RPC)
- generate a new key pair with no passphrase: `ssh-keygen -i id_rsa_EMS`
- shutdown EMS and take out MicroSD-Card
- mount root partition on /mnt
- `cp id_rsa_EMS.pub /mnt/root/.ssh/authorized_keys`
- `umount /mnt`
- insert MicroSD into EMS and restart EMS
- test login via ssh and public/private key:
  `ssh -o "KexAlgorithms +diffie-hellman-group1-sha1" -i id_rsa_EMS root@<ip_of_your_router>`
- test connection to XmlRPC: `telnet <ip_of_your_router> 20000`  


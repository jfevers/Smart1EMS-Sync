This project aims to read out data from an Energy Management System (EMS) from german company named "Smart1". This device can be found in e.g. battery systems called "GreenRock" from austrian company "BlueSky".

My motivation is to get live values into my home automation (OpenHAB2) and to safely store energy data in a database to analyse it with Grafana for example. All this without any cloud software from third parties. (It is my device, so it is my data.)

The project consist of two different building blocks:
- XmlRpc2Mqtt: Call the well-defined XML-RPC-API on TCP port 20000 and send that data as JSON to your own MQTT broker. Useful subscrbe from any home automation like FHEM, OpenHAB, Node-Red, ...
- TransferCounter: Download intern statistic files (CSV as FileDB) and insert them into MariaDB, MySQL, ...

The service SyncSmart1EMS will put both parts together and run them in background, ideally as docker container. (near future)

The current state is, that two seperate tools (Test*.py) exist to develope and run both parts seperatly. 


Access to EMS:
- take out MicroSD-Card
- copy your own ~/.ssh/id_rsa_pub to /root/.ssh/authorized_keys 
- insert MicroSD and restart EMS
- add TCP-forwarding to router: 22 -> 192.168.1.184:22 (SSH)
- add TCP-forwarding to router: 20000 -> 192.168.1.184:20000 (XML-RPC)

Todos:
- SyncXMLRPC: integrate TransferCounter
- TransferCounter: remove literal '2020' (till end of this year :-) )
- TransferCounter: get file for name mapping from EMS (copy and filter smart1.conf)
- TransferCounter: integrate longterm-statistics
- Document setup procedure
- Document OpenHab2 stuff

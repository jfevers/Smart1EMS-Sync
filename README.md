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
- SyncXMLRPC: integrate TransferCounter
- Transfercounter: fix coding issu in samrt1.conf
- TransferCounter: integrate longterm-statistics
- Document setup procedure
- Document OpenHab2 stuff


# Setup
Prepare access to EMS (the router is the one before the EMS, not your internat access router):
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


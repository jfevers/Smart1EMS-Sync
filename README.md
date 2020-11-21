
Access to EMS:
- take out MicroSD-Card
- copy /root/.ssh/authorized_keys from other computer
- insert MicroSD and restart EMS
- add TCP-forward to router: 22 -> 192.168.1.184:22
- add to personal .ssh/config:
host 10.0.0.4
 KexAlgorithms +diffie-hellman-group1-sha1
 User root


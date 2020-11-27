import datetime;
import dateutil.tz
import mysql.connector



ts = 1606477542

dt = datetime.datetime.utcfromtimestamp(ts)
#dt = dt.fromtimestamp(ts,dateutil.tz.gettz('CET'))


print(dt)
print(dt.tzname())
dtUtc = dt.astimezone(dateutil.tz.gettz('UTC'))
print(dtUtc)
print(dtUtc.tzname())
strSimple = dt.isoformat()
strUtc = dtUtc.strftime('%Y-%m-%d %H:%M:%S')

mydb = mysql.connector.connect(host="lala", user="EMSrw", password="NMe47u27gzsa",  database="EMSdata")
mycursor = mydb.cursor()

mycursor.execute("DROP TABLE IF EXISTS TzTest")
mycursor.execute("CREATE TABLE TzTest (time datetime PRIMARY KEY, value double)")
mydb.commit()
mycursor.execute("INSERT INTO TzTest (time, value) VALUES ('{}',{})".format(strUtc,42.0))

mydb.commit()
mydb.close()
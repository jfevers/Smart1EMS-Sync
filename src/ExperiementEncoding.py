



def cleanUtfSeqences(strIn):
    strClean = ''
    i=0
    while i < len(strIn):
        if strIn[i] == chr(92) and strIn[i+1] == chr(120):
            bb = strIn[i+2:i+4]
            c = chr(int(bb, 16))
            i = i+4
        else:
            c = strIn[i]
            i = i+1
        strClean =strClean + c 
    return strClean

with open("/home/friso/Unsafed/EMS-Data/Name-mapping.txt") as f:
    for strSeltsam in f:
        strSchoen = cleanUtfSeqences(strSeltsam)
        print(strSchoen)



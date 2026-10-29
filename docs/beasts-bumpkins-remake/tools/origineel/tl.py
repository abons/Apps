import sys
sys.path.insert(0,'E:/')
import mapread,struct
BASE='C:/Users/Axel/AppData/Local/Temp/claude/E--werk-androidApps-Apps/16e99493-ac86-47c7-921f-1d215c266f51/scratchpad/missies/'
def tail(k):
    d=open(BASE+'mis/M%d.MIS'%k,'rb').read()
    m=mapread.load(BASE+'mis/M%d.MIS'%k)
    return d[-m['trailing']:], m

import struct,re,sys
sys.path.insert(0,'C:/Users/Axel/AppData/Local/Temp/claude/E--werk-androidApps-Apps/16e99493-ac86-47c7-921f-1d215c266f51/scratchpad/bb_original/maps')
import os
_c=os.getcwd();os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../bb_original'))
from mapread import rle,names
os.chdir(_c)
BASE='C:/Users/Axel/AppData/Local/Temp/claude/E--werk-androidApps-Apps/16e99493-ac86-47c7-921f-1d215c266f51/scratchpad/missies/'
def load(k):
    d=open(BASE+'mis/M%d.MIS'%k,'rb').read()
    name=d[8:72].split(b'\0')[0].decode('latin1');sx,sy=d[72],d[73];p=74
    tex=[];road=[];player=[];m1=[];m2=[]
    for y in range(sy):
        n=struct.unpack_from('<i',d,p)[0];p+=4
        row=rle(d[p:p+n],sx*12);p+=n
        for x in range(sx):
            r=row[x*12:x*12+12]
            tex.append(r[0]);road.append(r[1]);player.append(r[2]);m1.append(struct.unpack_from('<i',r,3)[0]);m2.append(struct.unpack_from('<i',r,8)[0])
    a,b2,cnt=struct.unpack_from('<iii',d,p);p+=12
    objs=[];raws=[]
    for i in range(cnt):
        f=d[p];p+=1
        if f==0:continue
        n=struct.unpack_from('<i',d,p)[0];p+=4
        data=rle(d[p:p+n],0x13A);p+=n
        extra=b''
        if struct.unpack_from('<i',data,236)[0]!=0:
            L=data[0xF0];data[236:236+L]=d[p:p+L];p+=L
        if data[212]==98:
            data[0x3C:0x3C+32]=d[p:p+32];p+=32
        if struct.unpack_from('<i',data,56)[0]!=0:
            data[0x38:0x3A]=d[p:p+2];p+=2
        raws.append(bytes(data))
        objs.append(dict(i=i,cls=data[0xD4],x=data[0xD8],y=data[0xD9],state=data[0xEA],owner=data[0xF7],sex=data[0xF4],frame=data[0xF9],gen=data[0xE5],goto=[data[0xDD],data[0xDE]],health=struct.unpack_from('<H',data,0x6E)[0]))
    return dict(name=name,size=(sx,sy),tex=tex,road=road,player=player,m1=m1,m2=m2,objs=objs,raws=raws,tail=d[p:])

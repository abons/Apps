import struct,re,json,collections
def rle(b,size):
    out=bytearray(size);j=k=0
    while j<len(b):
        t=b[j];j+=1
        if t: 
            if k<size: out[k]=t
            k+=1
        else:
            l=b[j];j+=1
            k=min(k+l,size)
    return out
def load(fn):
    d=open(fn,'rb').read();assert d[:3]==b'MAP'
    name=d[8:72].split(b'\0')[0].decode('latin1');sx,sy=d[72],d[73];p=74
    tiles=[]
    for y in range(sy):
        n=struct.unpack_from('<i',d,p)[0];p+=4
        row=rle(d[p:p+n],sx*12);p+=n
        for x in range(sx):
            r=row[x*12:x*12+12]
            tiles.append(dict(x=x,y=y,tex=r[0],road=r[1],player=r[2],m1=struct.unpack_from('<i',r,3)[0],u1=r[7],m2=struct.unpack_from('<i',r,8)[0]))
    a,b2,cnt=struct.unpack_from('<iii',d,p);p+=12
    objs=[]
    for i in range(cnt):
        f=d[p];p+=1
        if f==0:continue
        n=struct.unpack_from('<i',d,p)[0];p+=4
        data=rle(d[p:p+n],0x13A);p+=n
        if struct.unpack_from('<i',data,236)[0]!=0:
            L=data[0xF0];data[236:236+L]=d[p:p+L];p+=L
        if data[212]==98:
            data[0x3C:0x3C+32]=d[p:p+32];p+=32
        if struct.unpack_from('<i',data,56)[0]!=0:
            data[0x38:0x3A]=d[p:p+2];p+=2
        objs.append(dict(i=i,cls=data[0xD4],x=data[0xD8],y=data[0xD9],state=data[0xEA],owner=data[0xF7],sex=data[0xF4],frame=data[0xF9],gen=data[0xE5],fleeing=bool(data[0x106]),going=bool(data[0x11D]),goto=[data[0xDD],data[0xDE]]))
    return dict(name=name,size=[sx,sy],tiles=tiles,objects=objs,trailing=len(d)-p,hdr=[a,b2,cnt])
names={}
for l in open('objects_list.txt'):
    m=re.match(r'(\d+)\s+(\S.*?)\s+(\d+)\s*$',l)
    if m:names[int(m[1])]=m[2]
if __name__=='__main__':
    m=load('M1.MIS');print(m['name'],m['size'],m['trailing'],m['hdr'],len(m['objects']))
    print(collections.Counter(t['tex'] for t in m['tiles']).most_common())
    print(collections.Counter(t['road'] for t in m['tiles']).most_common(5),collections.Counter(t['player'] for t in m['tiles']).most_common(5))
    c=collections.Counter(o['cls'] for o in m['objects'])
    for k,v in c.most_common():print(k,names.get(k),v)

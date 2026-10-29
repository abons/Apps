import struct
def box(fn):
    d=open(fn,'rb').read(); assert d[:3]==b'BOX'
    p=8; out=[]
    while p<len(d):
        n=d[p:p+256].split(b'\0')[0].decode('latin1'); pa=d[p+256:p+512].split(b'\0')[0].decode('latin1')
        p+=512+16
        sz=struct.unpack_from('<i',d,p)[0]; p+=4
        out.append((n,pa,d[p:p+sz])); p+=sz
    return out
if __name__=='__main__':
    for n,pa,b in box('MISSIONS.BOX')[:40]: print(n,pa,len(b),b[:3],b[8:72].split(b'\0')[0])
    print(len(box('MISSIONS.BOX')))
    for n,pa,b in box('MISTEXT0.BOX')[:10]: print(n,pa,len(b),b[:100])

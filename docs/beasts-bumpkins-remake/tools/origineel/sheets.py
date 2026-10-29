import sys,os,glob
sys.path.insert(0,os.path.dirname(__file__))
from mfb import MFBFile, Palettes
from PIL import Image
pal=Palettes.PALETTE
info=[]
for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__),'*.MFB'))):
    n=os.path.basename(f)[:-4].lower()
    try:
        m=MFBFile(open(f,'rb').read(),pal)
    except Exception as e:
        print('ERR',n,e);continue
    k=len(m.entries)
    if k==0 or m.width*k>8000 or m.height>400: info.append((n,k,m.width,m.height,'skip'));continue
    sh=Image.new('RGBA',(m.width*k,m.height),(0,0,0,0))
    for i,e in enumerate(m.entries): sh.paste(e,(i*m.width,0))
    sh.save(os.path.join(os.path.dirname(__file__),'..','sheets',n+'.png'))
    info.append((n,k,m.width,m.height,''))
open(os.path.join(os.path.dirname(__file__),'..','sheets','_info.txt'),'w').write('\n'.join('%s frames=%d %dx%d %s'%i for i in info))

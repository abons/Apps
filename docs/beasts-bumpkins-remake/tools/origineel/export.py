import sys,json,re,struct,collections,os
sys.path.insert(0,'.')
from mis import *
from PIL import Image,ImageDraw
avg=json.load(open(BASE+'../map1/maptile_avg.json'))
m1=json.load(open(BASE+'../map1/map1.json'))
known={}
cnt=collections.defaultdict(collections.Counter)
for y in range(192):
    for x in range(192):
        t=m1['tex'][y][x];kd=m1['kinds'][y][x]
        if kd!='void': cnt[t][kd]+=1
for t,c in cnt.items(): known[t]=c.most_common(1)[0][0]
def frame(t): return t-119 if t>=234 else t
def kind_of(t):
    if t<=5: return 'grass'
    if 200<=t<=217 or t in (225,226): return 'forest'
    if t in known: return known[t]
    if 115<=t<=131 and (t+119) in known: return known[t+119]
    f=frame(t)
    if f<len(avg):
        best=None
        for kt,kk in known.items():
            kf=frame(kt)
            if kf>=len(avg) or kf==f: continue
            d=sum((a-b)**2 for a,b in zip(avg[f],avg[kf]))
            if best is None or d<best[0]: best=(d,kk)
        if best: return best[1]
    return 'other'
KC={'void':(0,0,0),'water':(40,70,200),'grass':(40,130,40),'forest':(10,70,20),'dirt':(150,100,50),'sand':(220,200,120),'rock':(150,150,150),'rockrim':(110,100,90),'other':(190,190,60),'special':(255,0,255)}
BUILD={1:'kerk',2:'boerenhut',47:'put',51:'boerderij',53:'bakkerij',54:'brouwerij',66:'stadhuis',69:'bouwersgilde',75:'toren',86:'tovenaarsgilde',113:'boerenhut',117:'bakkerij',118:'put',119:'boerderij',123:'bouwersgilde',124:'brouwerij',126:'stadhuis',127:'kerk',145:'boogschuttersgilde',146:'boogschuttersgilde',150:'minstreelsgilde',151:'minstreelsgilde',152:'ridderslgilde',153:'ridderslgilde',154:'gevangenis',155:'gevangenis',157:'stallen',158:'stallen',162:'tempel',175:'tovenaarsgilde',207:'voetvolkgilde',208:'voetvolkgilde',221:'uitkijkpost',225:'uitkijkpost'}
BUILD_SET=set(BUILD)
WALLS={29,122,129,130,169,170,219,220,199}
TRAPS={36,37,93}
ITEMS={25,159,160,161,172,174,176,177,178,192,193,198,200,211,212,213,214,217,210,7}
CTYPE={1:'timer',2:'cash>',3:'cash_b',4:'count>',5:'count<',6:'object_vernietigd',7:'object_op_plek',9:'type9',10:'object_bij_object',11:'type11',12:'object_opgepakt_door',13:'eenheid_bij_object',14:'object_gebruikt',205:'leeg'}
rx=re.compile(rb'([\x00-\xff])\xcd([\x00-\xff]{4})([\x00-\xff]{4})([\x00-\xff]{4})([\x00-\xff])\xcd\x01\x00\x00\x00',re.S)
tx=re.compile(rb'\[(mis\d+-\d+\.txt)\]',re.I)
TXT={}
for f in os.listdir(BASE+'txt'):
    TXT[f.upper()]=open(BASE+'txt/'+f,'rb').read().decode('latin1').replace('\r','').strip()
def conds(t):
    out=[]
    for x in rx.finditer(t,16640):
        ty=x.group(1)[0]
        if ty==205: continue
        out.append(dict(off=x.start(),type=ty,kind=CTYPE.get(ty,'?'),owner_or_a=struct.unpack('<I',x.group(2))[0],b=struct.unpack('<I',x.group(3))[0],c=struct.unpack('<I',x.group(4))[0],id=x.group(5)[0]))
    return out
def process(k):
    m=load(k);N=192;sx,sy=m['size']
    tex=m['tex']
    kinds=[kind_of(t) for t in tex]
    seen=[False]*(N*N);st=[]
    for i in range(N*N):
        x,y=i%N,i//N
        if (x in(0,N-1) or y in(0,N-1)) and tex[i]<=5: seen[i]=True;st.append(i)
    while st:
        i=st.pop();x,y=i%N,i//N
        for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):
            a,b=x+dx,y+dy
            if 0<=a<N and 0<=b<N:
                j=b*N+a
                if not seen[j] and tex[j]<=5: seen[j]=True;st.append(j)
    for i in range(N*N):
        if seen[i]: kinds[i]='void'
    kc=collections.Counter(kinds)
    nonvoid=[i for i in range(N*N) if kinds[i]!='void']
    xs=[i%N for i in nonvoid];ys=[i//N for i in nonvoid]
    bbox=[min(xs),min(ys),max(xs),max(ys)]
    landk=lambda kd: kd not in('void','water')
    land_total=sum(1 for kd in kinds if landk(kd))
    flags=[o for o in m['objs'] if o['cls']==98]
    names_flag={}
    for o,r in zip(m['objs'],m['raws']):
        if o['cls']==98:
            names_flag[o['i']]=r[0x3C:0x5C].split(b'\0')[0].decode('latin1')
    own=[o for o in flags if o['owner']==0]
    home=None;home_comp=0;home_k=collections.Counter()
    if own:
        o=own[0];s=o['y']*N+o['x'];vis={s};st=[s]
        while st:
            i=st.pop();x,y=i%N,i//N
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    a,b=x+dx,y+dy
                    if 0<=a<N and 0<=b<N:
                        j=b*N+a
                        if j not in vis and landk(kinds[j]): vis.add(j);st.append(j)
        home_comp=len(vis);home_k=collections.Counter(kinds[i] for i in vis)
        hx=[i%N for i in vis];hy=[i//N for i in vis];home=[min(hx),min(hy),max(hx),max(hy)]
    objs=[];vill=[];gens=[];crea=[];bld=[];flg=[]
    for o,r in zip(m['objs'],m['raws']):
        c=o['cls'];nm=names.get(c,'cls%d'%c)
        d=dict(i=o['i'],cls=c,name=nm,x=o['x'],y=o['y'],owner=o['owner'])
        if c==103:
            d['type']=r[0xF4];d['first']=r[0x40:0x50].split(b'\0')[0].decode('latin1') if r[0x41]!=205 else ''
            vill.append(d)
        elif c==104:
            d['grp']=r[0xF3];d['type']=r[0xF4];crea.append(d)
        elif c==171:
            d['spawn_cls']=r[0xE7];d['spawn_name']=names.get(r[0xE7]);d['p5']=r[0xE5];d['p6']=r[0xE6];d['sub']=r[0xF4];gens.append(d)
        elif c==98:
            d['village']=names_flag.get(o['i'],'');flg.append(d)
        if c in BUILD_SET: d['dutch']=BUILD[c];bld.append(d)
        objs.append(d)
    cl=collections.Counter(d['name'] for d in objs)
    cz=conds(m['tail'])
    tt=m['tail']
    texts=[]
    for x in tx.finditer(tt):
        pre=[c for c in cz if 0<x.start()-c['off']<=60]
        tid=x.group(1).decode(); texts.append(dict(id=tid,off=x.start(),cond=pre[-1] if pre else None,text=TXT.get(tid.upper(),'')))
    recs=[]
    for p in range(5):
        r=tt[p*3328:(p+1)*3328]
        recs.append(dict(name=r[8:40].split(b'\0')[0].decode('latin1'),cash=struct.unpack_from('<h',r,78)[0] if p<4 else None,pop_field=struct.unpack_from('<h',r,336)[0]))
    brief=TXT.get('M%d.TXT'%k,'')
    res=dict(mission=k,file_name=m['name'],size=[sx,sy],bbox_nonvoid=bbox,kind_counts=dict(kc),land_total=land_total,home_island=dict(tiles=home_comp,bbox=home,kinds=dict(home_k)),
      road_tiles=sum(1 for x in m['road'] if x),owned_tiles=sum(1 for x in m['player'] if x),
      players=recs,briefing=brief,object_summary=dict(cl),villages=flg,villagers=vill,generators=gens,creatures=crea,buildings=bld,
      conditions=cz,hint_texts=texts,objects=objs,trailing_bytes=len(tt))
    x0,y0,x1,y1=bbox;S=4
    W=(x1-x0+1)*S;H=(y1-y0+1)*S
    img=Image.new('RGB',(W,H),(0,0,0));px=img.load()
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            col=KC.get(kinds[y*N+x],(255,0,0))
            for dy in range(S):
                for dx in range(S): px[(x-x0)*S+dx,(y-y0)*S+dy]=col
    dr=ImageDraw.Draw(img)
    OC={0:(255,255,0),1:(255,60,60),2:(255,140,0),3:(255,0,200),4:(255,255,255)}
    for d in objs:
        c=d['cls'];x=(d['x']-x0)*S;y=(d['y']-y0)*S
        if x<0 or y<0 or x>=W or y>=H: continue
        if c in (0,5,6,134,94,79): col=(0,40,0);r_=1
        elif c==83: col=(200,30,30);r_=1
        elif c==103: col=OC.get(d['owner'],(255,255,255));r_=2
        elif c==104: col=(255,0,0);r_=2
        elif c==98: col=(0,255,255);r_=3
        elif c==171: col=(255,128,255);r_=2
        elif c in BUILD_SET: col=OC.get(d['owner'],(255,255,255));r_=3
        elif c in ITEMS: col=(255,215,0);r_=2
        elif c in WALLS: col=(90,90,90);r_=1
        elif c in TRAPS: col=(255,80,0);r_=1
        elif c in (143,144): col=(255,120,0);r_=1
        elif c==110 or c==111: col=(255,255,255);r_=1
        else: col=(200,200,200);r_=1
        dr.rectangle([x-r_,y-r_,x+r_,y+r_],fill=col,outline=(0,0,0) if r_>1 else None)
    img.save(BASE+'m%02d_layout.png'%k)
    json.dump(res,open(BASE+'m%02d.json'%k,'w'),indent=1)
    return res
if __name__=='__main__':
    ks=[int(a) for a in sys.argv[1:]] or range(1,31)
    for k in ks:
        r=process(k)
        print(k,r['bbox_nonvoid'],r['land_total'],r['home_island']['tiles'],r['kind_counts'])

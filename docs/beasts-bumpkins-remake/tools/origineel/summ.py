import json,collections,sys
for k in range(1,31):
    r=json.load(open('m%02d.json'%k))
    v0=collections.Counter(v['type'] for v in r['villagers'] if v['owner']==0)
    ven=collections.Counter((v['owner'],v['type']) for v in r['villagers'] if v['owner']!=0)
    fl=[(f['owner'],f['x'],f['y'],f['village']) for f in r['villages']]
    b=collections.Counter((b['owner'],b['name']) for b in r['buildings'])
    ge=[(g['x'],g['y'],g['spawn_cls'],g['sub'],g['p5'],g['p6']) for g in r['generators']]
    cr=collections.Counter((c['grp'],c['type'],c['owner']) for c in r['creatures'])
    it=collections.Counter(o['name'] for o in r['objects'] if o['cls'] in (159,160,161,172,174,176,177,178,192,193,198,200,211,212,213,214,217,210,25,179,190,191))
    cz=[(c['type'],c['owner_or_a'],c['b'],c['c'],c['id']) for c in r['conditions']]
    print('=== M%d'%k,r['size'],'cash',[p['cash'] for p in r['players'][:4]],'pop',r['players'][0]['pop_field'])
    print(' land',r['land_total'],'home',r['home_island']['tiles'],'kinds',{a:b2 for a,b2 in r['kind_counts'].items() if a!='void'})
    print(' vill0',dict(v0),'enemy vill',dict(ven))
    print(' flags',fl)
    print(' bld',dict(b))
    print(' gen',ge)
    print(' crea',dict(cr))
    print(' items',dict(it))
    print(' cond',cz)
    print(' hints',[(t['id'],(t['cond']['type'],t['cond']['owner_or_a'],t['cond']['b'],t['cond']['c']) if t['cond'] else None) for t in r['hint_texts']])
